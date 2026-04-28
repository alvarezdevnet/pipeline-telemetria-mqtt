import network
import time
import json
import machine
import dht
import secrets
import ssd1306
from machine import Pin, PWM, SoftI2C
from umqtt.simple import MQTTClient
import uasyncio as asyncio

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE RED Y BROKER 
# ---------------------------------------------------------
WIFI_SSID = secrets.SSID
WIFI_PASS = secrets.PASSWORD
MQTT_BROKER = secrets.MQTT_BROKER
MQTT_PORT = 1883
MQTT_CLIENT_ID = "ESP32_Alvarez"
MQTT_TOPIC_PUB = "sovereign/telemetria"

# ---------------------------------------------------------
# 2. CONFIGURACIÓN DE HARDWARE
# ---------------------------------------------------------
try:
    i2c = machine.SoftI2C(scl=Pin(22), sda=Pin(21))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
except Exception as e:
    print("⚠️ Error OLED:", e)
    oled = None

sensor_dht = dht.DHT11(Pin(5))

led_verde = Pin(19, Pin.OUT)
led_azul  = Pin(4, Pin.OUT)   
led_rojo  = Pin(23, Pin.OUT)

buzzer = PWM(Pin(18))
buzzer.freq(1000)
buzzer.duty(0) 

# VARIABLES GLOBALES
g_temp = 0
g_hum = 0
g_estado_texto = "INIT"
g_wifi_status = "..."

# ---------------------------------------------------------
# 3. LÓGICA DE ALARMA
# ---------------------------------------------------------
def gestionar_alertas(temp, hum):
    led_verde.value(0); led_azul.value(0); led_rojo.value(0); buzzer.duty(0)
    hay_problema = False
    estado_texto = "TODO OK"

    if hum > 70:
        led_azul.value(1)    
        buzzer.freq(1000); buzzer.duty(512)     
        estado_texto = "ALERTA HUMEDAD"
        hay_problema = True

    if temp > 24:
        led_rojo.value(1)    
        buzzer.freq(2000); buzzer.duty(512)     
        if hay_problema: estado_texto = "CRITICO (T+H)" 
        else: estado_texto = "ALERTA CALOR"
        hay_problema = True

    if not hay_problema:
        led_verde.value(1)  
    return estado_texto

# ---------------------------------------------------------
# 4. FUNCIONES AUXILIARES
# ---------------------------------------------------------
async def pitido_arranque():
    buzzer.freq(2000); buzzer.duty(512); await asyncio.sleep(0.1)
    buzzer.duty(0); await asyncio.sleep(0.1)
    buzzer.freq(2000); buzzer.duty(512); await asyncio.sleep(0.1)
    buzzer.duty(0)

def mostrar_oled(estado, t, h, wifi_status):
    if oled:
        oled.fill(0)
        oled.text("MQTT SECURE LAB", 0, 0) 
        oled.hline(0, 10, 128, 1)
        oled.text(f"T: {t}C  H: {h}%", 0, 20)
        oled.text(estado[:16], 0, 35)
        oled.text(f"Net: {wifi_status}", 0, 50)
        oled.show()

async def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"📡 Conectando a {WIFI_SSID}...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        intentos = 0
        while not wlan.isconnected():
            intentos += 1
            await asyncio.sleep(1)
            print(f".", end="")
            if intentos > 15:
                print("\n❌ Fallo WiFi")
                return False
    config = wlan.ifconfig()
    print(f"\n✅ WiFi Conectado! IP: {config[0]}")
    return True

def reconectar_mqtt():
    """Función robusta de reconexión CON AUTENTICACIÓN"""
    try:
        
        client = MQTTClient(
            MQTT_CLIENT_ID, 
            MQTT_BROKER, 
            port=MQTT_PORT,
            user=secrets.MQTT_USER,      # <--- IMPORTANTE
            password=secrets.MQTT_PASS   # <--- IMPORTANTE
        )
        client.connect()
        print(f"✅ Conectado al Broker: {MQTT_BROKER}")
        return client
    except OSError as e:
        print(f"⚠️ Error conexion MQTT ({MQTT_BROKER}): {e}")
        return None

# ---------------------------------------------------------
# 5. TAREAS ASÍNCRONAS 
# ---------------------------------------------------------
async def tarea_logica_y_mqtt(client):
    global g_temp, g_hum, g_estado_texto, g_wifi_status
    while True:
        try:
            try:
                sensor_dht.measure()
                g_temp = sensor_dht.temperature()
                g_hum = sensor_dht.humidity()
            except OSError:
                print("⚠️ Error lectura DHT11")

            g_estado_texto = gestionar_alertas(g_temp, g_hum)

            if client:
                payload = json.dumps({
                    "device": "ESP32-Alvarez",
                    "ip": network.WLAN(network.STA_IF).ifconfig()[0],
                    "temp": g_temp,
                    "hum": g_hum,
                    "status": g_estado_texto
                })
                try:
                    client.publish(MQTT_TOPIC_PUB, payload)
                    print(f"📤 Enviado: {payload}")
                    g_wifi_status = "MQTT ON"
                except OSError:
                    print("⚠️ Error enviando. Reintentando...")
                    g_wifi_status = "Err MQTT"
                    try: client.connect()
                    except: pass
            else:
                g_wifi_status = "No Broker"
                # Intentamos reconectar si no hay cliente
                client = reconectar_mqtt()

        except Exception as e:
            print(f"❌ Error en bucle lógico: {e}")
        await asyncio.sleep(2)

async def tarea_pantalla():
    while True:
        mostrar_oled(g_estado_texto, g_temp, g_hum, g_wifi_status)
        await asyncio.sleep(1)

# ---------------------------------------------------------
# 6. ORQUESTADOR PRINCIPAL
# ---------------------------------------------------------
async def main():
    print("--- INICIANDO SISTEMA IoT JOSE ALVAREZ (SECURE) ---")
    await pitido_arranque()
    if not await conectar_wifi():
        print("Reiniciando sistema en 5s...")
        await asyncio.sleep(5)
        machine.reset()
    
    client = reconectar_mqtt()

    asyncio.create_task(tarea_logica_y_mqtt(client))
    asyncio.create_task(tarea_pantalla())

    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Apagado manual.")
    except Exception as e:
        print("Error Fatal:", e)
        machine.reset()