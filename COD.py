#ghid controale:
#    delay: viteza de redare a intarzieriilor (delay-ului)
#    feedback: numarul de intarzieri (delay-uri)
#    mix: determina cantitatea semnalului intarziat (delay-ul) fata de semnalul de intrare

#ATTENTIONE!:
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

    # Delay effect
    if params['delay_on']:    #verifica daca efectul este activat (butonul de on/off din interfata)
        delay_samples = int((params['delay_ms'] / 1000) * sample_rate)    #convertim timpul de delay din secunde in esantioane
        feedback = params['feedback'] / 100    
        mix = params['mix'] / 100    #normalizam valoriile pt mix si feedback pentru a se incadra in intervalul 0-1
        
        delay_out = np.zeros_like(dry) #pregatim un vector delay_out care va contine rezultatul aplicarii delay-ului pentru fiecare esantion.
        for i in range(frames):    #iteram prin fiecare esantion audio din bloc
            read_index = (write_index - delay_samples + max_delay_samples) % max_delay_samples #calculam pozitia in buffer de unde trebuie citit semnalul intarziat.
            delayed_sample = delay_buffer[read_index]    #citim valoarea semnalului întârziat din buffer.
            current_sample = dry[i] + delayed_sample * feedback    #combinam semnalul initial cu cel intarziat, inmultit cu semnalul de feedback
            delay_buffer[write_index] = current_sample    # stocam în buffer noua valoare, care contine semnalul curent si partea de feedback
            write_index = (write_index + 1) % max_delay_samples    #incrementam pozitia de scriere în buffer
            delay_out[i] = dry[i] * (1 - mix) + delayed_sample * mix    #combinam semnalul intarziat cu cel neefectat, asa incat sa fie incadrat in parametrii mix-ului

        out = delay_out

    # Reverb effect
    if params['reverb_on']:    #verifica daca efectul este activat (butonul de on/off din interfata)
        reverb_out = np.copy(out)    #Facem o copie a semnalului actual
        for b, idx, delay_len in zip(reverb_buffers, reverb_indices, reverb_delays):    #calculam pozitia in buffer de unde trebuie citit semnalul întarziat
            for i in range(frames):    #iteram prin fiecare esantion din blocul audio.
                delayed_sample = b[idx]    #extragem valoarea întarziata
                b[idx] = 0.7 * reverb_out[i] + 0.3 * delayed_sample    #stocam in buffer o combinatie intre semnalul actual si cel intarziat, cu 30% feedback, asta produce un efect de "reflectie"
                reverb_out[i] += delayed_sample * 0.3    #adaugam la iesire componenta intarziata, cu 30%
                idx = (idx + 1) % delay_len    #avansam indexul pentru acel buffer de reverb
            reverb_indices[reverb_delays.index(delay_len)] = idx    #salvam noul index modificat în lista de indici, pentru a se actualiza in afara for-ului
        out = reverb_out

    outdata[:, 0] = out    #semnalul final este trimis spre iesire

# Funcții GUI
def update_delay(val):
    params['delay_ms'] = int(float(val))

def update_feedback(val):
    params['feedback'] = int(float(val))

def update_mix(val):
    params['mix'] = int(float(val))

def toggle_stream():
    global audio_stream, toggle_btn
    if audio_stream is None:
        audio_stream = sd.Stream(callback=audio_callback,
                                 channels=1,
                                 samplerate=sample_rate,
                                 blocksize=blocksize)
        audio_stream.start()
        toggle_btn.config(text="PORNESTE MICROFON")
    else:
        audio_stream.stop()
        audio_stream.close()
        audio_stream = None
        toggle_btn.config(text="PORNESTE MICROFON")

def toggle_reverb():
    params['reverb_on'] = not params['reverb_on']
    reverb_btn.config(text=f"Reverb: {'ON' if params['reverb_on'] else 'OFF'}")

def toggle_delay():
    params['delay_on'] = not params['delay_on']
    delay_btn.config(text=f"Delay: {'ON' if params['delay_on'] else 'OFF'}")

# Interfață
root = tk.Tk()
root.title("PROIECT EFECTE AUDIO")

ttk.Label(root, text="Delay Time (ms)").pack()
delay_slider = ttk.Scale(root, from_=50, to=1000, orient='horizontal', command=update_delay)
delay_slider.set(params['delay_ms'])
delay_slider.pack()

ttk.Label(root, text="Feedback (%)").pack()
feedback_slider = ttk.Scale(root, from_=0, to=95, orient='horizontal', command=update_feedback)
feedback_slider.set(params['feedback'])
feedback_slider.pack()

ttk.Label(root, text="Mix (%)").pack()
mix_slider = ttk.Scale(root, from_=0, to=100, orient='horizontal', command=update_mix)
mix_slider.set(params['mix'])
mix_slider.pack()

delay_btn = ttk.Button(root, text="Delay: OFF", command=toggle_delay)
delay_btn.pack(pady=5)

reverb_btn = ttk.Button(root, text="Reverb: OFF", command=toggle_reverb)
reverb_btn.pack(pady=5)

toggle_btn = ttk.Button(root, text="PORNESTE MICROFON", command=toggle_stream)
toggle_btn.pack(pady=10)

root.mainloop()
