# Kalibrierung nach dem Shimming

Stand 2026-08-23, schwarzes PETG.

## Ergebnis

    z-Offset  0.26
    PEI-Platte beim Auflegen KRÄFTIG ANDRÜCKEN

## Wie der Wert gefunden wurde

Nach dem Aufbringen der Kapton-Shims stimmte die aus dem Profil
gerechnete Vorhersage nicht mehr — +0.07 kratzte über die Platte,
obwohl die Mitte gar kein Kapton bekommen hatte und dort angetastet
wird. Der Wert wurde deshalb empirisch von oben eingekreist:

In der Reihenfolge der Versuche:

| # | Offset | Auflage der Platte | Ergebnis |
|---|---|---|---|
| 1 | +0.07 | angedrückt | kratzt |
| 2 | +0.25 | nur aufgelegt | zu niedrig |
| 3 | +0.30 | angedrückt | gleichmäßig, aber zu hoch |
| 4 | +0.27 | angedrückt | zu weit weg, unregelmäßig |
| 5 | +0.25 | angedrückt | noch zu dicht |
| 6 | **+0.26** | **angedrückt** | **gut** |

Zwischen Versuch 4 und 5 wurde an einigen Stellen Kapton ergänzt.

## Die Platte muss angedrückt werden

Die Tabelle enthält einen scheinbaren Widerspruch: Versuch 2 mit +0.25
kam tiefer heraus als Versuch 4 mit +0.27, obwohl der Offset niedriger
ist. Das ist rechnerisch unmöglich, wenn sich nur der Offset ändert —
die Platte selbst muss sich bewegt haben. Der einzige Unterschied war,
dass sie in Versuch 2 nur aufgelegt und nicht angedrückt war.

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
