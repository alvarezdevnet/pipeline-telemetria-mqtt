# Pipeline de Telemetría MQTT

# Pipeline de Telemetría IoT  (Zero Trust Architecture)

![mqtt.png](mqtt.png)

Este repositorio proporciona la infraestructura completa para desplegar un sistema de telemetría IoT de grado empresarial. La arquitectura captura métricas ambientales (temperatura y humedad) a través de un nodo Edge (ESP32) y asegura el transporte de los datos utilizando el protocolo MQTT sobre TLS. Posteriormente, la información es orquestada en Node-RED, persistida en InfluxDB para el análisis de series temporales, y monitorizada en tiempo real mediante dashboards en Grafana, incorporando un sistema de notificaciones críticas vía Telegram.

El diseño destaca por su arquitectura **Security-First**. Para mitigar riesgos, el entorno implementa segmentación de red mediante VLANs (aislando los dispositivos IoT), cifrado de datos en tránsito, y políticas de autenticación estricta. Además, se garantiza un acceso remoto seguro sin exponer puertos públicos al exterior, utilizando **Cloudflare Zero Trust** como proxy inverso hacia la Raspberry Pi. Para respaldar esta infraestructura y asegurar la confianza de las conexiones de extremo a extremo, el sistema se apoya en un dominio personalizado que permite la validación oficial de certificados SSL/TLS.

---

## Arquitectura del Sistema

El flujo de los datos sigue este "pipeline":

1. **Edge (Hardware):** Un ESP32 lee el sensor DHT11 y publica la telemetría en formato JSON.
2. **Broker (Mosquitto):** Recibe los mensajes en el topic `sovereign/telemetria`.
3. **Procesamiento (Node-RED):** Actúa como el cerebro. Filtra datos, formatea para la base de datos y evalúa si hay que disparar alarmas.
4. **Almacenamiento (InfluxDB):** Base de datos de series temporales (Time-Series Database) para guardar el histórico.
5. **Visualización (Grafana):** Se conecta a InfluxDB para mostrar los datos en dashboards interactivos.
6. **Alertas (Telegram):** Node-RED envía notificaciones a un Bot si se superan los umbrales de seguridad.

![nodered.png](nodered.png)

---

## 💻 Hardware Utilizado

- Placa base: **ESP32**
- Sensor: **DHT11** (Temperatura y Humedad)
- Pantalla: **OLED SSD1306** (Conexión I2C)
- Actuadores: **Buzzer** (Alarma sonora) y **LEDs** (Indicadores de estado RGB)

![esp32_MQTT.jpg](esp32_MQTT.jpg)

---

## 📦 Stack de Software (Docker)

Toda la infraestructura del servidor corre sobre una Raspberry Pi (o servidor Linux) utilizando `docker-compose`. Los servicios están aislados en una red virtual llamada `iot-net`.

- `eclipse-mosquitto:latest` (Puerto 1883)
- `nodered/node-red:latest` (Puerto 1880)
- `influxdb:1.8` (Puerto 8086)
- `grafana/grafana-oss:latest` (Puerto 3000)

![grafana.png](grafana.png)

> Aqui vemos un ejemplo de las últimas 24 horas como desde la web monitorizo la temperatura y la humedad con alertas desde cualquier punto del planeta.
> 

---

## 📂 Estructura del Repositorio

El proyecto está organizado de la siguiente manera para separar la infraestructura (Docker) del código físico (MicroPython):

```
pipeline-telemetria-mqtt/
├── README.md                 # Esta documentación
├── docker/                   # Infraestructura de Servidor
│   ├── docker-compose.yml    # Orquestador de contenedores
│   ├── grafana-data/         # Volúmenes persistentes
│   ├── influxdb-data/
│   ├── mosquitto/
│   │   ├── config/
│   │   │   └── mosquitto.conf
│   │   └── data/
│   └── node-red/
│       └── flows.json        # Copia de seguridad de los flujos
├── scripts/                  # Scripts de automatización y utilidades
└── src/                      # Código fuente
    └── esp32_sensor/         # Código MicroPython para el nodo IoT
        ├── main.py           # Lógica principal del sensor
        ├── secrets.example.py# Plantilla de credenciales WiFi/MQTT
        └── ssd1306.py        # Driver de la pantalla OLED
```

## 🔒 Capa de Seguridad Implementada

Este laboratorio cumple con altos estándares de seguridad para IoT:

1. **Segmentación de Red:** El dispositivo IoT (ESP32) no tiene visibilidad del resto de la red local del hogar gracias a su aislamiento en una VLAN específica.
2. **Cifrado (TLS):** Los payloads de telemetría no viajan en texto plano; el ESP32 utiliza certificados TLS oficiales para comunicarse con el broker MQTT.
3. **Autenticación MQTT:** Acceso anónimo deshabilitado. Solo los clientes con credenciales válidas pueden publicar o suscribirse a los topics.
4. **Cloudflare Tunnel:** La Raspberry Pi actúa como servidor sin exponer puertos a Internet. Un demonio local (`cloudflared`) establece una conexión saliente segura hacia el dominio adquirido.

![TLS.png](TLS.png)

Encriptacion modo Full Estricta para respetar la maxima seguridad que nos ofrece el tunel.

---

## 🗺️ Roadmap / Próximos Pasos

Aunque el núcleo del sistema es completamente funcional y seguro, el proyecto sigue en evolución. Algunas posibles mejoras futuras incluyen:

- [ ]  Integración de un servidor local de DNS (Pi-hole/AdGuard) en la misma VLAN.
- [ ]  Incorporación de un segundo nodo ESP32 con sensores de calidad del aire (MQ-135).
- [ ]  Script de automatización (Bash) para realizar backups automáticos de los volúmenes de InfluxDB y Node-RED.
- [ ]  Se va a implementar próximamente la plataforma **Ignition** (Inductive Automation) para transformar este pipeline en una solución SCADA industrial completa.
- [ ]  **Visualización Perspective:** Creación de una HMI web y móvil de alto rendimiento compatible con estándares industriales.
- [ ]  **Scripts en Python:** Procesamiento de datos complejo en el servidor mediante el motor de scripting de Ignition.
- [ ]  **Reporting Engine:** Generación automática de reportes de estado y eficiencia del sistema.

---

## 👨‍💻 Autor

José Álvarez Domínguez Técnico de *Sistemas, Redes y Telemetría IoT*

- [Mi perfil de GitHub](https://github.com/TU_USUARIO)
- [Mi perfil de LinkedIn](https://linkedin.com/in/TU_USUARIO)

---

## 📄 Licencia

Este proyecto está bajo la Licencia **MIT**. Puedes usar, modificar y distribuir este código libremente, tanto para fines personales como comerciales, siempre y cuando se incluya la nota de copyright original.