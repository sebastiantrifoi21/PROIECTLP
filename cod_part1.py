#inainte de import se instaleaza sounddevices si numpy daca se primeste eroare
import sounddevice as sd
import numpy as np
import tkinter as tk
from tkinter import ttk

# Setări
sample_rate = 44100 # frecvența de eșantionare (numărul de mostre audio pe secundă)
blocksize = 1024 # cate eșantioane se proceseaza simultan

#dictionar cu parametrii initiali, reverb si delay fiind dezactivati
params = {
    'delay_ms': 300,
    'feedback': 50,
    'mix': 50,
    'reverb_on': False,
    'delay_on': False,
}

# Buffere
max_delay_samples = int(2 * sample_rate) #delay maxim de 2 secunde. cu 88200 esantioane
delay_buffer = np.zeros(max_delay_samples) #buffer circular care stochează mostrele audio întârziate
write_index = 0 #poziția curentă de scriere în buffer

# Parametri pentru reverb (scurt delay + feedback mic)
reverb_delays = [113, 337, 563, 797]  # în samples, numere prime pt dispersie
reverb_buffers = [np.zeros(d) for d in reverb_delays]
reverb_indices = [0 for _ in reverb_delays]

# Stream global
audio_stream = None

def audio_callback(indata, outdata, frames, time, status): #Este apelată automat de sounddevice
    global write_index, delay_buffer, reverb_buffers, reverb_indices

    dry = indata[:, 0]
    out = np.copy(dry)