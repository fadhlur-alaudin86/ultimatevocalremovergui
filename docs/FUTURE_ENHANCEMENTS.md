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

## 2. Rencana Implementasi Tahap 1 (Tertunda)

Rencana di bawah ini adalah eksekusi tahap awal yang telah dianalisis untuk dapat segera dipraktikkan tanpa merombak arsitektur, mencakup penambahan **Median Ensemble** dan **TTA untuk MDX-Net**. (Status: Menunggu eksekusi).

### `gui_data/constants.py`
- Tambahkan konstanta `MEDIAN_SPEC_SMOOTH = 'Median Spec Smooth'`.
- Tambahkan konstanta `MEDIAN_WAV_ALIGN = 'Median Wave Align'`.
- Masukkan konstanta baru ke dalam tupel `ENSEMBLE_TYPE` dan `MANUAL_ENSEMBLE_OPTIONS`.
- Tambahkan teks bantuan (GUI tooltip) untuk menjelaskan fitur Median.

### `lib_v5/spec_utils.py`
- **Fungsi `ensembling`**: Tambahkan percabangan logika untuk menghitung nilai tengah (`np.median(inputs_abs, axis=0)`) dari magnitudo spektrum, kemudian mengalikannya dengan *anchor phase* dari model utama.
- **Fungsi `ensemble_inputs`**: Daftarkan perutean untuk `MEDIAN_WAV_ALIGN`.
- **Fungsi `median_audio_align` (Baru)**: Buat fungsi baru untuk menerapkan pencarian *Median* (nilai tengah) pada gelombang sampel.

### `UVR.py`
- Buat dan letakkan `is_tta_Option` (Checkbox TTA) di bagian `mdx_opt_frame` agar MDX memiliki opsi TTA yang bisa diaktifkan dari antarmuka pengguna.
- Simpan dan ikat variabel state `is_tta` tersebut dengan setelan konfigurasi khusus MDX.

### `separate.py`
- Pada bagian fungsi `demix()` milik **MDX/MDXC** (saat masuk ke *loop* inferensi `model(batch)`):
  - Cek jika `self.is_tta` bernilai aktif (True).
  - Jika aktif, ciptakan tensor baru yang difase-balik (polaritas negatif): `inv_batch = -batch`.
  - Eksekusi model untuk versi tersebut: `x_inv = model(inv_batch)`.
  - Gabungkan hasil dengan rata-rata interferensi destruktif: `x = (x - x_inv) * 0.5`.

> **Peringatan Performa**: Mengaktifkan opsi TTA untuk MDX-Net akan meningkatkan kualitas secara signifikan, tetapi mengorbankan waktu pemrosesan yang akan menjadi **dua kali lipat lebih lambat**.
