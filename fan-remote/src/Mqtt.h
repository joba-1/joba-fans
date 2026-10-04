// Mqtt.h — MQTT control/state and Home Assistant discovery. See docs/spec.md for the topics.
#pragma once
#include <Arduino.h>

void mqttBegin();
void mqttLoop();
bool mqttConnected();
void mqttRecreateDiscovery(int oldGen);   // remove generation oldGen, announce the current one
void mqttRefreshDiscovery();   // names / enabled channels changed: tell Home Assistant now (any task)
