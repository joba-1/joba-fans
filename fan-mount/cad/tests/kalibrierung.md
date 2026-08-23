# Kalibrierung nach dem Shimming

Stand 2026-08-23, schwarzes PETG.

## Ergebnis

    z-Offset  0.25
    PEI-Platte beim Auflegen KRÄFTIG ANDRÜCKEN

## Wie der Wert gefunden wurde

Nach dem Aufbringen der Kapton-Shims stimmte die aus dem Profil
gerechnete Vorhersage nicht mehr — +0.07 kratzte über die Platte,
obwohl die Mitte gar kein Kapton bekommen hatte und dort angetastet
wird. Der Wert wurde deshalb empirisch von oben eingekreist:

| Offset | Auflage der Platte | Ergebnis |
|---|---|---|
| +0.07 | angedrückt | kratzt |
| +0.25 | nur aufgelegt | zu niedrig |
| +0.27 | angedrückt | zu weit weg, unregelmäßig |
| +0.30 | angedrückt | gleichmäßig, aber zu hoch |
| **+0.25** | **angedrückt** | **gut** |

## Die Platte muss angedrückt werden

Die Tabelle enthält einen scheinbaren Widerspruch: +0.25 kam tiefer
heraus als +0.27, obwohl der Offset niedriger ist. Das ist rechnerisch
unmöglich, wenn sich nur der Offset ändert — die Platte selbst muss
sich bewegt haben.

Der Unterschied zwischen "nur aufgelegt" und "kräftig angedrückt" ist
**größer als zwei Offset-Schritte**, also mehr als 0,05 mm. Das ist
mehr als die gesamte Restunebenheit nach dem Shimming.

Nach jedem Abnehmen der Platte also andrücken und das Mesh neu fahren,
sonst ist der Druck nicht mit dem vorherigen vergleichbar.

## Offene Frage

Warum +0.07 kratzte, ist ungeklärt. Die Mitte ist Antastpunkt und
bekam kein Kapton — dort hätte sich nichts ändern dürfen. Mögliche
Erklärungen: die Antastung liegt nicht exakt mittig, das Mesh
verrechnet die Gesamtfläche, oder das ringsum aufgefütterte Blech
hängt in der Mitte weniger durch als vorher.
