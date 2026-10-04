// Net.h — WiFi (WiFiManager portal), mDNS, NTP, ArduinoOTA.
#pragma once
#include <Arduino.h>

void netBegin();
void netLoop();
void netForgetWifi();   // erase credentials, reopen the setup portal
bool netConnected();
bool netPortalActive();   // the setup portal owns port 80 while this is true
