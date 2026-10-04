// Web.h — the one-page remote, its REST API and the SSE stream.
#pragma once
#include <Arduino.h>

void webBegin();
void webLoop();   // pushes state to SSE clients
