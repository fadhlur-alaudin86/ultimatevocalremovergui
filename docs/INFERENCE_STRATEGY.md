# Strategi Inferensi & Mode Ensemble Ultimate Vocal Remover (UVR)

Dokumen ini berisi panduan dan strategi terbaik (*best practices*) untuk mendapatkan hasil separasi audio berkualitas studio menggunakan Ultimate Vocal Remover. Strategi ini disusun berdasarkan keunggulan masing-masing arsitektur model (Roformer, SCNet, Demucs, MDX23C, dan VR).

---

## 🌟 Prinsip Utama: "Single Model First" (Jangan Paksakan Ensemble)

Dengan hadirnya arsitektur mutakhir seperti **Roformer (BS & MelBand)**, praktik *ensembling* **tidak lagi wajib** dan justru sering kali **tidak disarankan** sebagai langkah pertama. Mengapa?
Model-model terbaru ini memiliki kepresisian fasa (*phase preservation*) yang sangat luar biasa. Menyatukan mereka dengan model lain melalui *Average* atau *Min/Max* justru berisiko merusak fasa audio (membuat suara mendem, *comb-filtering*, atau tipis).

**Workflow Terbaik Saat Ini:**
1. **Selalu gunakan SATU model Roformer terbaik terlebih dahulu.**
2. Gunakan *Ensemble* **HANYA JIKA** hasil dari satu model tersebut masih menyisakan artifak, bocoran (*bleed*), atau kurang memuaskan pada frekuensi tertentu.

---

## 1. Strategi Ekstraksi: Vocals Only (Acapella Terbaik) & Keduanya (Vokal & Instrumen)

**Tujuan:** Mendapatkan vokal dan/atau instrumen yang jernih, penuh, natural, tanpa terpotong (*robotic*).

### 🏆 Model Utama (Sangat Disarankan, Tanpa Ensemble):
* **BS-Roformer (ViperX edition)**: Gunakan model ini sendirian. Model ini terbukti memiliki keseimbangan yang luar biasa untuk mengisolasi vokal tanpa merusak instrumen.

### ⚙️ Jika Hasil Masih Kurang (Mode Ensemble Darurat):
* Padukan dengan **MDX23C-InstVoc HQ** atau **Demucs v4**.
* **Algoritma Ensemble:** **`Average Align / Average Align`** atau **`Median Align / Median Align`**

---

## 2. Strategi Ekstraksi: Instrumental Only (Karaoke / Minus-One Murni)

**Tujuan:** Menghilangkan vokal utama dan vokal latar secara total.

### 🏆 Model Utama (Sangat Disarankan, Tanpa Ensemble):
* **MelBand Roformer (inst-v2)**: Gunakan model ini sendirian. Arsitektur *MelBand* sangat agresif dan dirancang khusus untuk membuang segala jenis suara manusia (termasuk desahan nafas dan harmoni).

### ⚙️ Jika Hasil Masih Kurang (Mode Ensemble Darurat):
* Padukan dengan **SCNet** (jika ketukan *kick drum* ikut menghilang) atau **5_HP-Karaoke-UVR** (jika masih ada sisa gema vokal).
* **Algoritma Ensemble:** **`Weighted Average / Weighted Average`** (Beri bobot MelBand 70%, model pelengkap 30%).

---

## 3. Strategi Ekstraksi: Keduanya Sekaligus (Vokal & Instrumen Seimbang)

**Tujuan:** Memisahkan *track* menjadi vokal dan instrumen di mana kedua hasilnya sama-sama pantas digunakan untuk *remix* atau *mastering* ulang, tanpa saling mengorbankan kualitas.

### 🏆 Model yang Disarankan:
1. **bs-roformer-viperx** (Isolasi tingkat dewa)
2. **htdemucs_ft** (Merapikan pemisahan bass, drum, dan melodi yang sering bocor ke fasa vokal)
3. **MDX23C-InstVoc HQ** (Transisi spektrum paling organik)

### ⚙️ Pengaturan Ensemble (Mode: 2 atau 3-Model Ensemble)
* **Algoritma Ensemble:** **`Average / Average`** atau **`Median Spec Smooth / Median Spec Smooth`**
  * *Mengapa?* Mode rata-rata biasa atau median yang dihaluskan (`Smooth`) menghindari perubahan ekstrem antar *frame* algoritma. Untuk penggunaan profesional (*stem mastering*), Anda tidak disarankan memakai `Min Spec` atau `Max Spec` karena itu akan mendistorsi sinyal asli. Anda membutuhkan penjumlahan matematis yang halus.
* **Overlap (MDX23C / MDX-Net):** Atur ke **8** atau maksimal.
  * Overlap yang tinggi akan membuat transisi irisan audio model MDX menjadi tidak terdengar.
* **TTA (Test-Time Augmentation):** **Aktifkan (ON)** untuk menghilangkan anomali paning (*stereo panning anomali*) yang terkadang muncul saat dua *stem* keras bertabrakan di frekuensi tengah.

---

## Ringkasan Eksekutif Pemilihan Model

| Target Ekstraksi | Prioritas Utama (Single Model) | Opsi Ensemble (Hanya Jika Dibutuhkan) | Algoritma Ensemble Terbaik | TTA |
| :--- | :--- | :--- | :--- | :--- |
| **Hanya Vokal** | BS-Roformer ViperX / MelBand | MDX23C-InstVoc HQ / Demucs v4 | `Average Align / Average Align` | ON |
| **Hanya Instrumental**| MelBand Roformer (inst-v2) | SCNet / VR Karaoke | `Weighted Average / Weighted Average` (70:30) | ON |
| **Vokal & Instrumen** | BS-Roformer ViperX | MDX23C-InstVoc HQ | `Median Spec Smooth / Median Spec Smooth` | ON |

> **Catatan:** Selalu sesuaikan *Chunk Size* dan *Overlap* dengan spesifikasi VRAM / RAM Anda. Jika Anda terpaksa melakukan Ensemble karena menemui kesulitan pada suatu trek, ingatlah bahwa menggabungkan model yang berat (seperti Roformer + SCNet) membutuhkan memori komputasi yang tinggi. Gunakan VRAM dengan bijak.
