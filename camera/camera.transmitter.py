import cv2
import mediapipe as mp
import serial
import time
import math
import numpy as np
from collections import deque

# ==========================================
# SİSTEM YAPILANDIRMASI
# ==========================================
SERIAL_PORT = "COM3"
BAUD_RATE = 115200
SMOOTHING_WINDOW = 3
THRESHOLD = 1

calib_data = {
    "min": [0.3] * 7,
    "max": [1.0] * 7
}

# ==========================================
# PARMAK → SERVO EŞLEŞTİRMESİ
# ==========================================
SERVO_MAP = [4, 2, 1, 0, 3]
INTERP_MAX = [360, 240, 240, 360, 360]

# ==========================================
# DONANIM BAŞLATMA
# ==========================================
try:
    esp = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    esp.setDTR(False)
    esp.setRTS(False)
    time.sleep(2)
    print("[BİLGİ] ESP bağlantısı başarıyla kuruldu.")
except Exception as e:
    print(f"[UYARI] Seri port bağlantı hatası: {e}")
    print("[BİLGİ] Sistem sadece simülasyon/görsel modda çalışacak.")
    esp = None

kamera = cv2.VideoCapture(0)
kamera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
kamera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

mp_el = mp.solutions.hands
el_modeli = mp_el.Hands(max_num_hands=1, min_detection_confidence=0.8, min_tracking_confidence=0.8)
mp_cizim = mp.solutions.drawing_utils
cizim_stili = mp.solutions.drawing_styles

aci_hafizasi = [deque(maxlen=SMOOTHING_WINDOW) for _ in range(5)]
son_gonderilen = [0, 0, 0, 0, 0]
parmak_isimleri = ["Basparmak", "Isaret", "Orta", "Yuzuk", "Serce"]

# ==========================================
# YARDIMCI FONKSİYONLAR
# ==========================================
def mesafe_hesapla(p1, p2):
    return math.sqrt((p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)

def get_finger_ratios(landmarks, w, h):
    lm = [[id, int(l.x * w), int(l.y * h)] for id, l in enumerate(landmarks)]
    referans = mesafe_hesapla(lm[5], lm[17])
    if referans == 0:
        referans = 1

    uclar  = [4, 8, 12, 16, 20]
    kokler = [0, 5,  9, 13, 17]

    current_ratios = []
    for i in range(5):
        dist = mesafe_hesapla(lm[uclar[i]], lm[kokler[i]])
        current_ratios.append(dist / referans)
    return current_ratios

def draw_transparent_ui(img, x, y, w, h, alpha=0.6):
    overlay = img.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (15, 15, 15), -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

# ==========================================
# KALİBRASYON RUTİNİ
# ==========================================
def calibrate(mode_text, color):
    samples = []
    start_time = time.time()

    while time.time() - start_time < 5:
        success, img = kamera.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        h, w, _ = img.shape
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = el_modeli.process(img_rgb)

        kalan_sure = int(5 - (time.time() - start_time))

        draw_transparent_ui(img, 30, 30, 450, 120, alpha=0.7)
        cv2.putText(img, f"KALIBRASYON MODU", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, f"GOREV: {mode_text}", (50, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
        cv2.putText(img, f"SURE: {kalan_sure} sn", (50, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

        if result.multi_hand_landmarks:
            ratios = get_finger_ratios(result.multi_hand_landmarks[0].landmark, w, h)
            samples.append(ratios)
            mp_cizim.draw_landmarks(
                img,
                result.multi_hand_landmarks[0],
                mp_el.HAND_CONNECTIONS,
                cizim_stili.get_default_hand_landmarks_style(),
                cizim_stili.get_default_hand_connections_style()
            )

        cv2.imshow("Robot El Kontrol Sistemi", img)
        cv2.waitKey(1)

    return np.mean(samples, axis=0)

# ==========================================
# ANA SÜREÇ
# ==========================================
print("[SİSTEM] 1. AŞAMA: ELİNİZİ TAMAMEN AÇIN VE BEKLEYİN...")
calib_data["max"] = calibrate("ELINIZI TAMAMEN ACIN", (0, 255, 0))

print("[SİSTEM] 2. AŞAMA: YUMRUK YAPIN VE BEKLEYİN...")
calib_data["min"] = calibrate("TAM YUMRUK YAPIN", (0, 0, 255))

print("[SİSTEM] Kalibrasyon tamamlandı! Gerçek zamanlı kontrol başlıyor...")

pTime = 0

while True:
    basarili, goruntu = kamera.read()
    if not basarili:
        break

    goruntu = cv2.flip(goruntu, 1)
    h, w, _ = goruntu.shape
    goruntu_rgb = cv2.cvtColor(goruntu, cv2.COLOR_BGR2RGB)
    sonuc = el_modeli.process(goruntu_rgb)

    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
    pTime = cTime

    draw_transparent_ui(goruntu, 20, 20, 320, 280, alpha=0.75)
    cv2.putText(goruntu, "ROBOT EL DURUMU", (40, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.line(goruntu, (40, 65), (300, 65), (100, 100, 100), 2)

    if sonuc.multi_hand_landmarks:
        for el_landmark in sonuc.multi_hand_landmarks:
            oranlar = get_finger_ratios(el_landmark.landmark, w, h)
            mevcut_acilar = []

            for i in range(5):
                aci = np.interp(
                    oranlar[i],
                    [calib_data["min"][i], calib_data["max"][i]],
                    [0, 180]
                )
                aci = int(np.clip(aci, 0, 180))

                aci_hafizasi[i].append(aci)
                yumusak_aci = int(sum(aci_hafizasi[i]) / len(aci_hafizasi[i]))
                mevcut_acilar.append(yumusak_aci)

                y_pos = 100 + (i * 35)
                cv2.putText(goruntu, f"{parmak_isimleri[i][:3]}:", (40, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)
                cv2.putText(goruntu, f"{yumusak_aci:03d}*", (260, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

                bar_x = 100
                bar_w = 140
                cv2.rectangle(goruntu, (bar_x, y_pos - 12), (bar_x + bar_w, y_pos), (80, 80, 80), 1)

                dolgu_w = int(np.interp(yumusak_aci, [0, 180], [0, bar_w]))
                renk_g  = int(np.interp(yumusak_aci, [0, 180], [0, 255]))
                renk_r  = int(np.interp(yumusak_aci, [0, 180], [255, 0]))

                if dolgu_w > 0:
                    cv2.rectangle(goruntu, (bar_x, y_pos - 12), (bar_x + dolgu_w, y_pos), (0, renk_g, renk_r), -1)

            # =====================================================
            # PARMAK REMAP + VERİ GÖNDERİMİ
            # =====================================================
            gonderilecek = [mevcut_acilar[SERVO_MAP[i]] for i in range(5)]

            if esp and any(abs(gonderilecek[i] - son_gonderilen[i]) > THRESHOLD for i in range(5)):
                veri = f"{gonderilecek[0]},{gonderilecek[1]},{gonderilecek[2]},{gonderilecek[3]},{gonderilecek[4]}\n"
                esp.write(veri.encode())
                son_gonderilen = gonderilecek.copy()

            mp_cizim.draw_landmarks(
                goruntu,
                el_landmark,
                mp_el.HAND_CONNECTIONS,
                cizim_stili.get_default_hand_landmarks_style(),
                cizim_stili.get_default_hand_connections_style()
            )

    else:
        cv2.putText(goruntu, "El tespit edilemedi...", (40, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, cv2.LINE_AA)

    draw_transparent_ui(goruntu, w - 200, 20, 180, 80, alpha=0.6)
    cv2.putText(goruntu, f"FPS: {int(fps)}", (w - 180, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
    durum_renk = (0, 255, 0) if esp else (0, 0, 255)
    durum_text = "ESP: Bagli" if esp else "ESP: Yok"
    cv2.putText(goruntu, durum_text, (w - 180, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, durum_renk, 2, cv2.LINE_AA)

    cv2.imshow("Robot El Kontrol Sistemi", goruntu)

    if cv2.waitKey(1) & 0xFF == 27:
        break

print("[SİSTEM] Kapatılıyor...")
kamera.release()
if esp:
    esp.close()
cv2.destroyAllWindows()
