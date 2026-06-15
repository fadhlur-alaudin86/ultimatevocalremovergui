# Future Enhancements & Implementation Plans

Dokumen ini berisi ide-ide penyempurnaan fitur dan kualitas untuk Ultimate Vocal Remover (UVR), yang diadaptasi dari metode *state-of-the-art* seperti pada repositori `Music-Source-Separation-Training` (MSST).

## 1. Ide Penyempurnaan dari MSST

### A. Metode Ensemble yang Lebih Maju
* **Median Ensemble (`median_wave` & `median_fft`)**: Menggunakan nilai tengah (`Median`) daripada `Average` (rata-rata) biasa. Secara matematis mengabaikan nilai ekstrem, sehingga jauh lebih stabil dan tahan terhadap *glitch* dari model yang buruk.
* **Weighted Ensemble (Ensemble Berbobot)**: Mengizinkan pengguna untuk mengatur rasio bobot setiap model. Ini memungkinkan penggabungan di mana model A (yang presisi) diberi bobot 70%, dan model B (sebagai pelengkap) berbobot 30%.

### B. Peningkatan Inferensi (*Test-Time Augmentation* & *BigShifts*)
* **Generic BigShifts**: Menerapkan pemotongan audio bergeser (seperti pada fitur *Shifts* di Demucs) ke **semua tipe model** (MDX dan VR). Ini secara drastis mengurangi *chunk boundary artifacts* (suara patah-patah/distorsi pada ujung potongan audio).
* **Advanced TTA (Test-Time Augmentation)**: Menerapkan *channel reversal* (menukar saluran kiri dan kanan) dan *polarity inversion* (mengubah fase audio menjadi negatif/terbalik), lalu merata-rata hasil pemrosesannya. TTA ini sangat andal untuk membatalkan *noise* asimetris yang dihasilkan model.

### C. Dukungan Arsitektur Model Generasi Baru
Menyediakan dukungan inferensi untuk arsitektur AI terbaru:
* **Mamba2 / State Space Models**: Lebih ringan pada memori VRAM namun mampu memberikan kualitas setara *Transformer* (Roformer).
* **SCNet / Bandit**: Sangat terkenal kemampuannya untuk pemisahan *stem* dengan transien tajam (seperti drum dan perkusi).

---

## 2. Implementasi yang Telah Selesai (Selesai Diimplementasikan)

Beberapa peningkatan dari repositori sumber (Music-Source-Separation-Training) telah berhasil diadaptasi ke dalam UVR:

### A. Dukungan Arsitektur Model Native
UVR kini secara langsung (*native*) mampu membaca dan mengeksekusi model berformat YAML tanpa perlu konversi format HuggingFace:
- **BS-Roformer & MelBand-Roformer**
- **SCNet**
- **Mamba2**
- **Bandit**

### B. Metode Ensemble yang Lebih Maju
- **Average Align / Smooth**: Menerapkan algoritma untuk menghaluskan dan meratakan fase sinyal dari beberapa model yang berbeda.
- **Weighted Ensemble**: Algoritma `Weighted Average` telah diimplementasikan penuh untuk merata-ratakan *output* dari berbagai model sesuai dengan rasio pembobotan (*weights*) yang dikalibrasi oleh pengguna.

### C. Advanced TTA (Test-Time Augmentation)
- Opsi **TTA** telah diaktifkan untuk model **MDX-Net / MDX23C**. Saat opsi ini dicentang, UVR akan melakukan inferensi ganda (*normal* dan polaritas terbalik `-batch`), lalu membatalkan anomali audio/glitch dengan menjumlahkan (*destructive interference*) sinyal sebelum diproses ulang menjadi *spectrogram*.

> **Peringatan Performa**: Mengaktifkan opsi TTA untuk MDX-Net akan meningkatkan kualitas separasi, tetapi mengorbankan waktu pemrosesan menjadi dua kali lipat lebih lambat.
