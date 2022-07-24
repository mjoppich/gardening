# gardening

Gardening App for Watering Plants using ESP8266

## Controls a pump for watering the flowers

A pump is attached via a relay to the ESP8266. At given times the webserver will tell the ESP8266 to activate the pump for a predefined interval.

The pump/alarm times can be configures via a web interface:

![Alarm Times](/images/times_alarm.png "Alarm Times")

## Weather Stats

The webserver records measured environment parameters from the BME280 sensor attached to the ESP8266. Temperature, air pressure and humidity are recored. The attached soil moisture sensor delivers the moisture of the soil.

For each of the values up to 1000 measurements are recorded and plottet interactively:

![Sensor Values](/images/times_plot.png "Sensor Values")

# Want to build your own gardening setup?

Besides some wires, those are the components I used:

* Solar Panel https://smile.amazon.de/gp/product/B099N95YGV/
* Solar Charger https://smile.amazon.de/gp/product/B07P85QZ7D/
* Battery
* BME280 https://smile.amazon.de/AZDelivery-GY-BME280-Barometrischer-Temperatur-Luftfeuchtigkeit/dp/B07D8T4HP6/
* Relay 3.3V https://smile.amazon.de/gp/product/B09HH8TY32/
* Soil Moisture sensor https://smile.amazon.de/Aideepen-Bodenfeuchtigkeitssensor-Hygrometer-Modul-korrosionsbest%C3%A4ndiges-Arduin0-Pflanzenbew%C3%A4sserung/dp/B08GCRZVSR/
* ESP8266 https://smile.amazon.de/AZDelivery-NodeMCU-ESP8266-ESP-12E-Development/dp/B074Q2WM1Y/
* Pump https://smile.amazon.de/gp/product/B09HKPGBCP/
