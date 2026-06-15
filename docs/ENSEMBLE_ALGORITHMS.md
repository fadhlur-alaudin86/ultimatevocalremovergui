# Panduan Algoritma Ensemble di Ultimate Vocal Remover (UVR)

Mode Ensemble di UVR memungkinkan Anda menggabungkan hasil (output) dari dua atau lebih model AI yang berbeda untuk mendapatkan hasil ekstraksi yang lebih baik, menutupi kelemahan satu model dengan kekuatan model lainnya.

## Bagaimana Cara Kerjanya?

UVR memisahkan audio menjadi dua bagian utama:
1. **Primary Stem:** Biasanya adalah **Vokal** (suara utama yang ingin diekstrak).
2. **Secondary Stem:** Biasanya adalah **Instrumental** (suara latar/musik pendamping).

Setiap opsi algoritma ensemble memiliki penamaan dengan format **`[Algoritma Primary Stem] / [Algoritma Secondary Stem]`**.
Misalnya, **`Max Spec / Min Spec`** (atau sering disingkat **`Max/Min`**) berarti:
- **Max Spec** diterapkan untuk mengekstrak **Primary Stem (Vokal)**.
- **Min Spec** diterapkan untuk mengekstrak **Secondary Stem (Instrumental)**.

## Penjelasan Masing-Masing Operasi Matematis

Ada tiga jenis operasi dasar yang digunakan dalam ensemble UVR:

1. **Max Spec (Nilai Maksimum)**
   - Mengambil bagian spektrogram dengan suara/magnitude paling keras dari semua model secara bin-demi-bin.
   - **Efek jika digunakan pada Vokal:** Memastikan tidak ada bagian vokal yang terpotong atau hilang. Sangat kuat mempertahankan badan dan keutuhan suara penyanyi.
   - **Kelemahan:** Memperbesar risiko *bleed* (suara musik ikut bocor/masuk ke dalam vokal).

2. **Min Spec (Nilai Minimum)**
   - Mengambil bagian spektrogram dengan suara/magnitude paling pelan dari semua model.
   - **Efek jika digunakan pada Instrumental:** Sangat agresif menghapus sisa vokal yang bocor ke instrumental, menghasilkan track instrumental yang sangat bersih.
   - **Kelemahan:** Jika digunakan terlalu agresif, pemotongan spektrogram bisa merusak kelanjutan fasa suara asli dan memotong frekuensi instrumen, membuatnya terdengar tipis, memiliki efek gemericik air (*musical noise*), atau "bolong".

3. **Audio Average (Rata-rata)**
   - Secara matematis merata-rata hasil gelombang suara dari semua model (`(Sinyal A + Sinyal B) / n`).
   - **Efek:** Merupakan metode yang paling natural dan halus. Tidak menyebabkan pemotongan frekuensi/fasa yang ekstrem atau agresif.
   - **Kelemahan:** Jika dua model menghasilkan fase suara yang berlawanan (*out-of-phase*), merata-ratakannya bisa menyebabkan volume suara turun (*phase cancellation*) atau terdengar mendem/tertahan (*comb-filtering*).

4. **Weighted Average (Rata-rata Berbobot)**
   - Seperti *Audio Average*, namun memungkinkan setiap model memiliki "bobot" atau pengaruh yang berbeda.
   - **Efek:** Memungkinkan Anda memberikan prioritas lebih tinggi pada model yang terbukti memiliki kualitas vokal lebih jernih (misal 70%), dan menggunakan model lain hanya sebagai pelengkap untuk mengisi detail yang hilang (misal 30%).
   - **Kelemahan:** Masih rentan terhadap masalah *phase cancellation* jika bobot tidak disetel dengan baik.

5. **Average Align (Rata-rata dengan Penyelarasan)**
   - Melakukan penyelarasan fasa antar model terlebih dahulu sebelum dirata-rata. Algoritma mencari letak puncak frekuensi dan mencocokkannya.
   - **Efek:** Memecahkan masalah *phase cancellation* yang sering terjadi pada `Average` biasa. Sangat berguna jika Anda menggabungkan model yang memproses audio dengan tingkat penundaan (latensi) mikroskopis yang berbeda.
   
6. **Smooth (Penghalus)**
   - Meratakan output dengan menghindari transisi nilai yang tiba-tiba (*abrupt changes*). Algoritma menggunakan perata-rataan berbasis rentang/jendela waktu kecil.
   - **Efek:** Sangat cocok untuk menghilangkan artifak *glitch* digital atau suara "kresek" kecil yang kadang dihasilkan oleh salah satu model. Vokal akan terdengar lebih bulat.

## Rekomendasi Penggunaan Terbaik

### 1. Terbaik untuk Vokal Saja (Acapella)
Jika prioritas utama Anda adalah mengambil vokal bersih:
- **Paling Bersih (No Bleed): `Min/Max` atau `Min/Ave`**
  Vokal di-filter secara agresif (`Min Spec`) untuk menghapus segala kebocoran musik. Risiko: vokal mungkin sedikit tipis atau terdengar seperti robot.
- **Paling Natural & Penuh: `Ave/Max` atau `Ave/Ave`**
  Menjaga kehangatan suara asli penyanyi tanpa pemotongan fasa yang kasar. Direkomendasikan jika model yang dipakai memang sudah berkualitas.

### 2. Terbaik untuk Instrumen Saja (Karaoke / Minus-One)
Jika prioritas Anda adalah membuat lagu instrumental:
- **Paling Bersih (Vocal Removal): `Max/Min` atau `Ave/Min`**
  Instrumental di-filter secara agresif (`Min Spec`) untuk membersihkan sisa desahan nafas dan gema (*reverb*) vokal yang membandel.
- **Paling Kaya Suara (Fullness): `Max/Ave` atau `Ave/Ave`**
  Digunakan jika lagu memiliki instrumen padat (seperti distorsi gitar) dan Anda tidak ingin suara instrumen tersebut ikut terpotong atau meredup.

### 3. Terbaik untuk Keduanya Sekaligus (Vokal & Instrumen)
- **Juara Bertahan Paling Aman: `Ave/Ave`**
  Karena `Average` tidak secara ekstrem memotong bin spektrogram seperti `Min` atau `Max`, metode ini meminimalisir artifak digital. Transisi fasa antar model jauh lebih mulus. Baik vokal maupun instrumen akan terdengar paling mendekati kualitas rekaman asli.
- **Alternatif Agresif (Untuk Lagu Susah): `Min/Min`**
  Untuk genre musik *Heavy Metal* atau EDM yang sangat padat/berisik di mana vokal dan instrumen bertabrakan di frekuensi yang sama. Memaksa kedua stem saling membuang suara yang bocor satu sama lain dengan konsekuensi suara mungkin sedikit *muffled* (tertahan).

---
**💡 Tips Pro UVR:**
Jika Anda melakukan ensemble menggunakan dua model modern kelas atas (seperti *MDX-Net Roformer* digabungkan dengan *Demucs HT*), Anda sangat disarankan untuk selalu memulai dengan **`Ave/Ave`**. Model-model modern ini sudah memiliki tingkat separasi yang sangat presisi, sehingga memaksa algoritma agresif seperti `Min` atau `Max` justru berisiko merusak kejernihan yang sudah berhasil dicapai oleh model itu sendiri.
