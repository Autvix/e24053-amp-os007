
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import snap7 as snap7
import snap7.util as su
import threading
import asyncio
import csv
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import pandas as pd


# Configurar o cliente Snap7
client = snap7.client.Client()

# Variável para status da conexão
connected = False
simulacao_ativa = False
rodando = True


# Variaveis para Simulação
nivelSH = 0.0
ft_103 = 0.0
intlk_lc = True
intlk_LL = True
FT_CFW = [0.0] * 601    
FT_103 = [0.0] * 301
FT = [0.0] * 901
FT_SINTER = [0.0] * 901
FI_CFW = 0.0
new_SP = 0.0
media_FT = 0.0
media_sinter = 0.0
nivel_fut = 0.0
Lmin = 0.0
Lmax = 0.0
ganho = 0.0
new_SP_2 = 0.0

dadosEntrada = []

#//////////////////////////////////////////////////////////////////////////
#                     **Funções para o PLC**
#/////////////////////////////////////////////////////////////////////////
# Função para conectar ao PLC
def connect_to_plc():
    global connected
    try:
        client.connect('172.18.31.10', 0, 2)  # IP, Rack, Slot
        if client.get_connected():
            connected = True
            messagebox.showinfo("Conexão", "Conectado ao PLC com sucesso!")
            status.config(text="Conectado")
        else:
            messagebox.showerror("Conexão", "Falha ao conectar ao PLC.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao conectar: {e}")

# Função para desconectar do PLC
def disconnect_from_plc():
    global connected
    try:
        if client.get_connected():
            client.disconnect()
            connected = False
            messagebox.showinfo("Conexão", "Desconectado do PLC.")
            status.config(text="Desconectado")
        else:
            messagebox.showinfo("Conexão", "Já está desconectado.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao desconectar: {e}")

# Função para escrever na DB
def write_to_db(db_number, start_address, size, value):
    if not connected:
        messagebox.showerror("Erro", "Não há conexão com o PLC.")
        return

    try:
        # Obter valores dos campos
        fdb_number = int(db_number)
        fstart_address = int(start_address)
        fsize = int(size)
        fvalue = float(value)

        # Criar o buffer
        data = bytearray(fsize)

        # Configurar o valor no buffer
        su.set_real(data, 0, fvalue)

        # Escrever na DB
        client.db_write(fdb_number, fstart_address, data)
        #messagebox.showinfo("Sucesso", f"Valor {value} escrito na DB{db_number}.DBD{start_address}.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao escrever na DB: {e}")


def read_to_db(db_number, start_address, size):
    if not connected:
       messagebox.showerror("Erro", "Não há conexão com o PLC.")
       return 
    
    try:
        data = client.db_read(db_number, start_address, size)
        value = su.get_real(data, 0)
        return value
    
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler na DB: {e}")
        

def send_DB():
    db = db_entry.get()
    ad = address_entry.get()
    s = size_entry.get()
    v = value_entry.get()
    write_to_db(db, ad, s, v)

    
#//////////////////////////////////////////////////////////////////////////
#                     **Funções para o Simulação**
#/////////////////////////////////////////////////////////////////////////
def text_sel(event):
    """Callback para abrir o pop-up ao clicar no texto."""
    text_id = event.widget.find_closest(event.x, event.y)[0]  # Pega o ID do texto clicado
    change_value(text_id)
    
        
def change_value(text_id):
    """Função que cria e exibe o pop-up personalizado."""
    # Criar uma nova janela (pop-up)
    popup = tk.Toplevel(root)
    popup.title("Alterar valor")
    popup.geometry("300x200")
    popup.configure(bg="lightgray")

    # Rótulo no pop-up
    tk.Label(popup, text="Insira um valor:", font=("Arial", 12), bg="lightgray").pack(pady=10)

    # Entrada de valor
    entrada_valor = tk.Entry(popup, font=("Arial", 12), width=20)
    entrada_valor.pack(pady=5)

    # Função para associar o valor
    def save():
        valor = entrada_valor.get()
        if valor:
            canvas.itemconfig(text_id, text=valor)
            
            popup.destroy()
        else:
            tk.messagebox.showwarning("Aviso", "Insira um valor antes de salvar!")

    # Botão para salvar o valor
    tk.Button(popup, text="Salvar", font=("Arial", 12), command=save).pack(pady=10)

    # Botão para fechar o pop-up
    tk.Button(popup, text="Fechar", font=("Arial", 12), command=popup.destroy).pack(pady=5)



def control(event):
    global connected
    
    def change_mode(value):
        text_id2 = event.widget.find_closest(event.x, event.y)[0]
        
        if text_id2 == 16:
            # Controlador de vazao
            if connected:
                if value:
                    #Envia para DB setar em auto
                    bit_data1 = bytearray(1)
                    su.set_bool(bit_data1, 0, 2, 1)
                    client.db_write(1000, 28, bit_data1)
                    
                    auto_button.config(fg="blue")
                    man_button.config(fg="black")
                else:
                    #Envia para DB setar em man
                    bit_data1 = bytearray(1)
                    su.set_bool(bit_data1, 0, 3, 1)
                    client.db_write(1000, 28, bit_data1)
                    
                    auto_button.config(fg="black")
                    man_button.config(fg="blue")
            else:
                tk.messagebox.showwarning("Aviso", "PLC não conectado")
                
        elif text_id2 == 24:
            # Controlador de nivel
            if connected:
                if value:
                    #Envia para DB setar em auto
                    bit_data1 = bytearray(1)
                    su.set_bool(bit_data1, 0, 0, 1)
                    client.db_write(1000, 28, bit_data1)
                    
                    auto_button.config(fg="blue")
                    man_button.config(fg="black")
                else:
                    #Envia para DB setar em man
                    bit_data1 = bytearray(1)
                    su.set_bool(bit_data1, 0, 1, 1)
                    client.db_write(1000, 28, bit_data1)
                    
                    auto_button.config(fg="black")
                    man_button.config(fg="blue")
            else:
                tk.messagebox.showwarning("Aviso", "PLC não conectado")
    
    """ Pop up para o controlador"""
    # Cria janela de pop up
    popup = tk.Toplevel(root)
    popup.title("Controlador")

    popup.geometry("300x200")
    popup.configure(bg="lightgray")
    
    frame1 = tk.Frame(popup, bg="lightblue", bd=2, relief="solid")
    frame1.pack(fill="both", padx=5, pady=5)
    frame2 = tk.Frame(popup, bg="lightblue", bd=2, relief="solid")
    frame2.pack(fill="both", padx=5, pady=5)
    frame3 = tk.Frame(popup, bg="lightblue", bd=2, relief="solid")
    frame3.pack(fill="both", padx=5, pady=5)
    
    valor_in = canvas.itemcget(vel_text, "text")
    valor_setpoint = canvas.itemcget(vel_text, "text")
    valor_mv = canvas.itemcget(vel_text, "text")
    
    # IN
    tk.Label(frame1, text="IN:", font=("Arial", 14)).pack(pady=5, side="left", padx=10)
    tk.Label(frame1, text=valor_in, font=("Arial", 14)).pack(pady=5, side="top", padx=20)

    # Setpoint
    tk.Label(frame2, text="SP:", font=("Arial", 14)).pack(pady=5,  side="left", padx=10)
    tk.Label(frame2, text=valor_setpoint, font=("Arial", 14)).pack(pady=5,  side="top", padx=20)

    # MV
    tk.Label(frame3, text="MV:", font=("Arial", 14)).pack(pady=5,  side="left", padx=10)
    tk.Label(frame3, text=valor_mv, font=("Arial", 14)).pack(pady=5,  side="top", padx=20)

    # Botões MAN e AUTO
    man_button = tk.Button(popup, text="MAN", command=lambda: change_mode(False), width=15)
    man_button.pack(side="left", padx=(25,10), pady=5)
    auto_button = tk.Button(popup, text="AUTO", command=lambda: change_mode(True), width=15)
    auto_button.pack(side="left", padx=10, pady=5)
    

def control_level(event):
    global connected
    global new_SP
    global media_FT
    global media_sinter
    global nivel_fut
    global Lmin
    global Lmax
    global ganho
    
    def change_mode(value):
        text_id2 = event.widget.find_closest(event.x, event.y)[0]
                
        if text_id2 == 24:
            # Controlador de nivel
            if connected:
                if value:
                    #Envia para DB setar em auto
                    bit_data1 = bytearray(1)
                    su.set_bool(bit_data1, 0, 0, 1)
                    client.db_write(1000, 28, bit_data1)
                    
                    auto_button.config(fg="blue")
                    man_button.config(fg="black")
                else:
                    #Envia para DB setar em man
                    bit_data1 = bytearray(1)
                    su.set_bool(bit_data1, 0, 1, 1)
                    client.db_write(1000, 28, bit_data1)
                    
                    auto_button.config(fg="black")
                    man_button.config(fg="blue")
            else:
                tk.messagebox.showwarning("Aviso", "PLC não conectado")
    
    """ Pop up para o controlador"""
    # Cria janela de pop up
    popup = tk.Toplevel(root)
    popup.title("Controle de Nivel")

    popup.geometry("350x450")
    popup.configure(bg="lightgray")
    
    frame1 = tk.Frame(popup, bg="lightblue", bd=2, relief="solid")
    frame1.pack(fill="both", padx=5, pady=5)
    frame2 = tk.Frame(popup, bg="lightblue", bd=2, relief="solid")
    frame2.pack(fill="both", padx=5, pady=5)
    frame3 = tk.Frame(popup, bg="lightblue", bd=2, relief="solid")
    frame3.pack(fill="both", padx=5, pady=5)
    frame4 = tk.Frame(popup, bg="lightblue", bd=2, relief="solid")
    frame4.pack(fill="both", padx=5, pady=5)
    frame5 = tk.Frame(popup, bg="lightblue", bd=2, relief="solid")
    frame5.pack(fill="both", padx=5, pady=5)
    frame6 = tk.Frame(popup, bg="lightblue", bd=2, relief="solid")
    frame6.pack(fill="both", padx=5, pady=5)
    frame7 = tk.Frame(popup, bg="lightblue", bd=2, relief="solid")
    frame7.pack(fill="both", padx=5, pady=5)
    
    # Novo Setpoint
    tk.Label(frame1, text="New_SP:", font=("Arial", 14)).pack(pady=5, side="left", padx=10)
    new_sp_label = tk.Label(frame1, text=new_SP, font=("Arial", 14))
    new_sp_label.pack(pady=5, side="top", padx=20)

    # Vazao media dos 15 min
    tk.Label(frame2, text="Md Vazao:", font=("Arial", 14)).pack(pady=5,  side="left", padx=10)
    media_FT_label = tk.Label(frame2, text=media_FT, font=("Arial", 14))
    media_FT_label.pack(pady=5,  side="top", padx=20)

    # Vazao media de saida da tremonha
    tk.Label(frame3, text="Md saida:", font=("Arial", 14)).pack(pady=5,  side="left", padx=10)
    media_sinter_label = tk.Label(frame3, text=media_sinter, font=("Arial", 14))
    media_sinter_label.pack(pady=5,  side="top", padx=20)

    # Nivel futuro
    tk.Label(frame4, text="Nivel Fut:", font=("Arial", 14)).pack(pady=5,  side="left", padx=10)
    nivel_fut_label = tk.Label(frame4, text=nivel_fut, font=("Arial", 14))
    nivel_fut_label.pack(pady=5,  side="top", padx=20)

    # Ganho
    tk.Label(frame5, text="Ganho:", font=("Arial", 14)).pack(pady=5,  side="left", padx=10)
    ganho_label = tk.Label(frame5, text=ganho, font=("Arial", 14))
    ganho_label.pack(pady=5,  side="top", padx=20)

    # Limite Minimo do Setpoint
    tk.Label(frame6, text="Lmin:", font=("Arial", 14)).pack(pady=5,  side="left", padx=10)
    Lmin_label = tk.Label(frame6, text=Lmin, font=("Arial", 14))
    Lmin_label.pack(pady=5,  side="top", padx=20)

    # Limite Maximo do Setpoint
    tk.Label(frame7, text="Lmax:", font=("Arial", 14)).pack(pady=5,  side="left", padx=10)
    Lmax_label = tk.Label(frame7, text=Lmax, font=("Arial", 14))
    Lmax_label.pack(pady=5,  side="top", padx=20)

    # Botões MAN e AUTO
    man_button = tk.Button(popup, text="MAN", command=lambda: change_mode(False), width=15)
    man_button.pack(side="left", padx=(25,10), pady=5)
    auto_button = tk.Button(popup, text="AUTO", command=lambda: change_mode(True), width=15)
    auto_button.pack(side="left", padx=10, pady=5)

    def update():
        new_sp_label.config(text=new_SP)
        media_FT_label.config(text=media_FT)
        media_sinter_label.config(text=media_sinter)
        nivel_fut_label.config(text=nivel_fut)
        ganho_label.config(text=ganho)
        Lmin_label.config(text=Lmin)
        Lmax_label.config(text=Lmax)

        popup.after(1000, update)

    update()


def import_txt(event):
    global FT_103
    global FT_CFW
    global FI_CFW
    global FT
    global FT_SINTER
    global nivelSH
    
    try:
        with open("Vetor_FT103.csv", mode="r") as file1:
            # Divide os valores e converte para float
            reader = csv.reader(file1)
            for row in reader:
                FT_103 = [float(valor) for valor in row]
        
        with open("FI_CFW.csv", mode="r") as file2:
            # Divide os valores e converte para float
            reader = csv.reader(file2)
            for row in reader:
                FI_CFW = float(row[0])
        
        with open("nivelSH.csv", mode="r") as file3:
            # Divide os valores e converte para float
            reader = csv.reader(file3)
            for row in reader:
                nivelSH = float(row[0])
        
        with open("Vetor_FT.csv", mode="r") as file4:
            # Divide os valores e converte para float
            reader = csv.reader(file4)
            for row in reader:
                FT = [float(valor) for valor in row]
        
        with open("Vetor_FTSINTER.csv", mode="r") as file5:
            # Divide os valores e converte para float
            reader = csv.reader(file5)
            for row in reader:
                FT_SINTER = [float(valor) for valor in row]
        
        with open("Vetor_FTCFW.csv", mode="r") as file6:
            # Divide os valores e converte para float
            reader = csv.reader(file6)
            for row in reader:
                FT_CFW = [float(valor) for valor in row]
                return FT_CFW
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler vetor: {e}")

           

def toggle_simulacao(event):
    global simulacao_ativa

    if simulacao_ativa:
        simulacao_ativa = False
        canvas.itemconfig(lig_des_text, text="Ligar Simulação")
        canvas.itemconfig(lig_des_button, fill="lightgreen")
    else:
        simulacao_ativa = True
        canvas.itemconfig(lig_des_text, text="Desligar Simulação")
        canvas.itemconfig(lig_des_button, fill="red")

        
async def Simulacao():
    global simulacao_ativa
    global ft_103
    global intlk_lc
    global intlk_LL
    global nivelSH
    
    global FT_CFW
    global FT_103
    global FT
    
    global new_SP
    global media_FT
    global media_sinter
    global nivel_fut
    global Lmin
    global Lmax
    global ganho
    global new_SP_2

    #Pegar da DB
    global FI_CFW
    #FC103 = 0
    
    #Saida
    FT_CFWM = 0
    FT_103M = 0
    

    while rodando:
        if simulacao_ativa:
            if intlk_lc:
            # ********************************************
            # 	Simulação da Vazão das CFW's até a CT103
            # ********************************************
            
                media_CFW = 0.0
                media_CT103 = 0.0
                
                for i in range(599):
                    i = i + 1
                    if rodando:
                        FT_CFW[i] = round(FT_CFW[i + 1], 5)
                        media_CFW = media_CFW + ( (FT_CFW[i + 1] - media_CFW) / i)
                        #time.sleep(0.1)
                    else:
                        i = 599
                
                FT_CFW[600] = FI_CFW
                
            # ******************************************
            # 	  Simulação da Vazão da CT103 até a S/H	
            # ******************************************
                for j in range(299):
                    j = j + 1
                    if rodando:
                        FT_103[j] = FT_103[j + 1]
                        media_CT103 = media_CT103 + ( (FT_103[j + 1] - media_CT103) / j)
                       # time.sleep(0.1)
                    else:
                        j = 299
                
                ft_103 = FT_103[1]
                ft_cfw_fc = FT_CFW[1]
                FT_103[300] = FT_CFW[1]
                
                FT_CFWM = media_CFW
                FT_103M = media_CT103
                
                
            # ******************************************
            # 	  Simulação da Vazão de saida do SH	
            # ******************************************
            if intlk_LL:
                velocidade = float(canvas.itemcget(vel_text, "text"))
            else:
                velocidade = 0.0
            
            altura = float(canvas.itemcget(high_text, "text"))
            densidade = float(canvas.itemcget(density_text, "text"))
            largura = float(canvas.itemcget(width_text, "text"))
            umidade = float(canvas.itemcget(humidity_text, "text"))
            
            sinter = velocidade * (altura / 1000.0) * densidade * largura * 60 * (1 + (umidade / 100.0))
            silo_sec = velocidade * (80.0 / 1000.0) * densidade * largura * 60 * (1 + (umidade / 100.0))
            
            vz_total_sinter = round(sinter + silo_sec, 3)
            
            
            """    
            Simulação do nivel da tremonha
            """
            capTremonha = float(canvas.itemcget(volume_text, "text"))
            
            
            # ******************************************
            # 	  Simulação do Nivel do SH
            # ******************************************
            Entrada = (intlk_lc * ft_103) / 3600.0
            Saida = sinter / 3600.0
            
            nivelSH = nivelSH + ((Entrada - Saida) / (capTremonha * densidade)*100.0)
            if nivelSH < 0:
                nivelSH = 0.0
            elif nivelSH > 100:
                nivelSH = 100.0
            
            
            # ******************************************
            # 	  Cálculo do novo Setpoint
            # ******************************************
            media_FT = 0.0
            media_sinter = 0.0

            for v in range(899):
                v = v + 1
                if rodando:
                    FT[v] = FT[v + 1]
                    FT_SINTER[v] = FT_SINTER[v + 1]
                    media_FT = media_FT + ( (FT[v + 1] - media_FT) / v)
                    media_sinter = media_sinter + ( (FT_SINTER[v + 1] - media_sinter) / v)
                   # time.sleep(0.1)
                else:
                    v = 899
                    
            FT[900] = FI_CFW
            FT_SINTER[900] = sinter 
            Tempo = 900
            histerese = float(canvas.itemcget(histerese_text, "text"))

            if velocidade > 0:
                Lmin = max(sinter - histerese, 0)
                Lmax = min(sinter + histerese, 950)
            else:
                Lmin = float(canvas.itemcget(Lmin_text, "text"))
                Lmax = float(canvas.itemcget(Lmin_text, "text"))
                #Lmax = min(Lmin + 300, 950)
            
            SP = float(canvas.itemcget(SP_text, "text"))
            ganho = float(canvas.itemcget(ganho_text, "text"))
            volume_md = (media_FT*(Tempo/3600))/densidade
            
            """
            nivel_fut = min(max(((((nivelSH/100)*capTremonha)+volume_md)-((media_sinter*(Tempo/3600))/densidade))*(100/capTremonha), 0),100)
            new_SP = min(max(Lmin + (((SP - nivel_fut)/100) + ganho)*ft_103, Lmin),Lmax)
            """

            if FT_SINTER[1] == 0:
                nivel_fut = min(max(((((nivelSH/100)*capTremonha)+volume_md)-((sinter*(Tempo/3600))/densidade))*(100/capTremonha), 0),100)
                new_SP = min(max(Lmin + (((SP - nivel_fut)/100) + ganho)*ft_103, Lmin),Lmax)
            else:
                nivel_fut = min(max(((((nivelSH/100)*capTremonha)+volume_md)-((media_sinter*(Tempo/3600))/densidade))*(100/capTremonha), 0),100)
                new_SP = min(max(Lmin + (((SP - nivel_fut)/100) + ganho)*ft_103, Lmin),Lmax)

            #time.sleep(0.1)
            sinter_round = round(sinter, 3)
            nivelSH_round = round(nivelSH, 2)
            ft_103_round = round(ft_103, 3)
            ft_cfw_round = round(ft_cfw_fc, 3)
            fi_cfw_round = round(FI_CFW, 3)
            md_ftcfw_round = round(FT_CFWM, 3)
            md_ct103_round = round(FT_103M, 3)
            new_SP_round = round(new_SP, 3)
            md_sinter_round = round(media_sinter, 3)
            md_FT_round = round(media_FT, 3)


            # Atualiza Campos
            canvas.itemconfig(FT_OutTot_text, text=f"{vz_total_sinter}")
            canvas.itemconfig(FT_OutSH_text, text=f"{sinter_round}")
            canvas.itemconfig(FT_InSH_text, text=f"{ft_103_round}")
            canvas.itemconfig(FT_103_text, text=f"{ft_cfw_round}")
            canvas.itemconfig(FT_CFW_text, text=f"{fi_cfw_round}")
            canvas.itemconfig(nivelSH_text, text=f"{nivelSH_round}")
            canvas.itemconfig(intlk_text, text=f"{new_SP}")
            
            if connected:
                # ******************************************
                # 	          Envia para a DB
                # ******************************************
                # Simualação ativa
                bit_data1 = bytearray(1)
                su.set_bool(bit_data1, 0, 0, simulacao_ativa)
                client.db_write(1000, 0, bit_data1)

                # Interlock
                bit_data2 = bytearray(1)
                su.set_bool(bit_data2, 0, 0, intlk_lc)
                client.db_write(1000, 6, bit_data2)
                
                # Nivel do SH
                write_to_db(1000, 2, 4, nivelSH_round)
                
                # Vazao FC-103
                write_to_db(1000, 8, 4, ft_cfw_round)
                
                # Media vazao esteira CFW
                #write_to_db(1000, 30, 4, md_ftcfw_round)
                
                # Media vazao esteira CT 103
                #write_to_db(1000, 34, 4, md_ct103_round)
                
                # Media vazao total entrada
                # write_to_db(1000, 48, 4, md_FT_round)
                
                # Media vazao saida
                # write_to_db(1000, 52, 4, md_sinter_round)
                
                # Novo setpoint de vazao
                # write_to_db(1000, 66, 4, new_SP_round)
                
                # Saída da tremonha
                write_to_db(1000, 54, 4, sinter_round)
                
                # Entrada da tremonha
                write_to_db(1000, 16, 4, ft_103_round)
                
                # Vazão das CFWs
                write_to_db(1000, 58, 4, fi_cfw_round)
                
                
                # ******************************************
                # 	          Recebe da DB
                # ******************************************
                # Interlock LC
                #bit_data2 = client.db_read(1000, 6, 1)
                #value2 = su.get_bool(bit_data2, 0, 0)            
                #intlk_lc = value2
                
                # Velocidade da esteira da máquina de sinter
                vel_esteira= round(read_to_db(1000, 62, 4), 3)
                canvas.itemconfig(vel_text, text=vel_esteira)
                
                # Setpoint da tremonha
                spt_tremonha = round(read_to_db(1000, 20, 4), 3)
                canvas.itemconfig(SP_text, text=spt_tremonha)
                
                # Densidade
                density = round(read_to_db(1000, 66, 4), 3)
                canvas.itemconfig(density_text, text=density)
                
                # Umidade
                umidade_db = round(read_to_db(1000, 70, 4), 3)
                canvas.itemconfig(humidity_text, text = umidade_db)
                
                # Ganho
                ganho_db = round(read_to_db(1000, 74, 4), 3)
                canvas.itemconfig(ganho_text, text = ganho_db)
                                
                # Histerese
                histerese_db = round(read_to_db(1000, 78, 4), 3)
                canvas.itemconfig(histerese_text, text = histerese_db)

                # Novo setpoint
                new_SP_2 = read_to_db(1000, 50, 4)
                
                
                # Vazao CFW
                #FI_CFW = read_to_db(1000, 12, 4)
                
            
            if intlk_lc == False:
                actual_color = canvas.itemcget(intlk_form, "fill")
                new_color = "yellow" if actual_color == "" else ""
                canvas.itemconfig(intlk_form, fill=new_color)
            else:
                canvas.itemconfig(intlk_form, fill="")
        
        else:
            if connected:
                bit_data1 = bytearray(1)
                su.set_bool(bit_data1, 0, 0, simulacao_ativa)
                client.db_write(1000, 0, bit_data1)
                
    
        await asyncio.sleep(0.75)        


async def vazao():
    global simulacao_ativa
    global intlk_lc
    global intlk_LL
    global new_SP
    global FI_CFW
    global nivelSH

    global new_SP_2

    global dadosEntrada

    name_csv = 'WIQ-1118_2.csv'
    resultado_csv = 'resultados_newsp.csv'
    
    dadosEntrada = pd.read_csv(name_csv, sep=',', encoding='latin-1', low_memory=False)
    
    # Selecionar os valores da linha 2 até a linha 17000, na segunda coluna (índice 1) e converter para float
    dadosEntrada = dadosEntrada.iloc[1:17000, 1].apply(pd.to_numeric, errors='coerce').tolist() 
    
    i = 0
    
    # Criar/limpar o arquivo e adicionar o cabeçalho
    with open(resultado_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['NEW_SP'])  # Cabeçalho do CSV


    while rodando:
        if simulacao_ativa:
            if nivelSH >= 88:
                intlk_lc = False
            elif nivelSH <= 82:
                intlk_lc = True

            if nivelSH <= 22:
                intlk_LL = False
            elif nivelSH >= 25:
                intlk_LL = True

            if intlk_lc:
                if i <= 17000:
                    FI_CFW = dadosEntrada[i]
                    i = i + 1
                else:
                    i = 0

            # Gravar o valor imediatamente no arquivo CSV
            with open(resultado_csv, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([new_SP_2])

        await asyncio.sleep(1)



#//////////////////////////////////////////////////////////////////////////
#                     **Graficos - Tendencias**
#/////////////////////////////////////////////////////////////////////////
def open_graphic(tipo):
    global nivelSH
    global new_SP
    """
    Abre uma nova janela do Matplotlib com um gráfico de tendência em tempo real.
    O gráfico muda dependendo do tipo (1 ou 2).
    """
    # Inicializar os dados
    x_data = list(range(7200))  # Eixo X fixo com 20 pontos
    y_data = [0] * 7200         # Eixo Y inicializado com zeros

    # Configurar Matplotlib
    fig, ax = plt.subplots()
    ax.set_title(f"Gráfico de Tendência {tipo}")
    ax.set_xlabel("Tempo")
    ax.set_ylabel("Valor")
    linha, = ax.plot(x_data, y_data, lw=2)

    # Configurar o limite fixo do eixo X e intervalo Y
    ax.set_xlim(0, 19)
    ax.set_ylim(0, 10)

    def atualizar(frame):
        """Atualiza o gráfico com novos dados."""
        # Gerar novos valores dependendo do tipo do gráfico
        if tipo == 1:
            ax.set_ylim(0, 110)
            ax.set_xlim(0, 7200)
            novo_valor = nivelSH  # Gráfico 1: nivel da SH
        elif tipo == 2:
            ax.set_ylim(0, 1000)
            ax.set_xlim(0, 7200)
            novo_valor = new_SP  # Gráfico 2: novo setpoint
        elif tipo == 3:
            ax.set_ylim(0, 1000)
            ax.set_xlim(0, 7200)
            novo_valor = float(canvas.itemcget(FT_InSH_text, "text"))
        elif tipo == 4:
            ax.set_ylim(0, 1000)
            ax.set_xlim(0, 7200)
            novo_valor = float(canvas.itemcget(FT_OutSH_text, "text"))
            
        # Atualizar os dados
        y_data.append(novo_valor)
        y_data.pop(0)

        # Atualizar a linha do gráfico
        linha.set_ydata(y_data)

        return linha,

    # Criar animação
    ani = animation.FuncAnimation(fig, atualizar, interval=500)

    # Exibir o gráfico
    plt.show()



#//////////////////////////////////////////////////////////////////////////
#                     **Interface Gráfica com Tkinter**
#/////////////////////////////////////////////////////////////////////////
# Interface Gráfica
root = tk.Tk()
root.title("Interface PLC")
root.geometry("900x700")

# Criação de Abas
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# Adicionar Frames
aba1 = ttk.Frame(notebook)
aba2 = ttk.Frame(notebook)
aba3 = ttk.Frame(notebook)
aba4 = ttk.Frame(notebook)

# Adicionar Frames ao notebook
notebook.add(aba1, text="Conexão")
notebook.add(aba2, text="Operações")
notebook.add(aba3, text="Simulação")
notebook.add(aba4, text="Sobre")

#--------------------------------------------------------------------------
#                             Conteudo ABA 1
#--------------------------------------------------------------------------
ttk.Label(aba1, text="Configuração de Conexão", font=("Arial", 14)).pack(pady=20)

# Botão para conectar ao PLC
connect_button = tk.Button(aba1, text="Conectar ao PLC", command=connect_to_plc, width=20)
connect_button.pack(pady=10)

# Botão para desconectar do PLC
disconnect_button = tk.Button(aba1, text="Desconectar do PLC", command=disconnect_from_plc, width=20)
disconnect_button.pack(pady=10)

# Rótulo para exibir o valor atual
status = tk.Label(aba1, text="Desconectado", font=("Arial", 14))
status.pack(pady=20)



#--------------------------------------------------------------------------
#                             Conteudo ABA 2
#--------------------------------------------------------------------------
ttk.Label(aba2, text="Operações no PLC", font=("Arial", 14)).grid(row=0, column=0, padx=5, pady=5)
aba2.grid_columnconfigure(0, weight=0)  # Rótulos
aba2.grid_columnconfigure(1, weight=0) 

# Campo para a DB
tk.Label(aba2, text="Número da DB:").grid(row=2, column=0, padx=(10, 0), pady=5, sticky="w")
db_entry = tk.Entry(aba2, width=15)
db_entry.grid(row=2, column=1, padx=(0, 1), pady=5, sticky="w")

# Campo para o endereço
tk.Label(aba2, text="Endereço na DB:").grid(row=3, column=0, padx=(10, 0), pady=5, sticky="w")
address_entry = tk.Entry(aba2, width=15)
address_entry.grid(row=3, column=1, padx=(0, 1), pady=5, sticky="w")

# Campo para o tamanho
tk.Label(aba2, text="Tamanho (bytes):").grid(row=4, column=0, padx=(10, 0), pady=5, sticky="w")
size_entry = tk.Entry(aba2, width=15)
size_entry.grid(row=4, column=1, padx=(0, 1), pady=5, sticky="w")

# Campo para o valor a ser escrito
tk.Label(aba2, text="Valor a escrever:").grid(row=5, column=0, padx=(10, 0), pady=5, sticky="w")
value_entry = tk.Entry(aba2, width=15)
value_entry.grid(row=5, column=1, padx=(0, 1), pady=5, sticky="w")

# Botão para escrever na DB
write_button = tk.Button(aba2, text="Escrever na DB", command=send_DB, width=20)
write_button.grid(row=9, column=0, padx=10, pady=5, sticky="w")



#--------------------------------------------------------------------------
#                             Conteudo ABA 3
#--------------------------------------------------------------------------
# Canvas para layout
canvas = tk.Canvas(aba3, bg="gray", width=900, height=610)
canvas.pack(fill="both", expand=True)

# Título
canvas.create_text(450, 30, text="SIMULAÇÃO TREMONHA", font=("Arial", 24, "bold"), fill="black")

#Interlock
intlk_form = canvas.create_rectangle(400, 90, 500, 140, fill="",outline="black")
intlk_text = canvas.create_text(450, 115, text="Interlock", font=("Arial", 10, "bold"))
canvas.tag_bind(intlk_text, "<Button-1>", lambda e: open_graphic(2))

# Containers visuais (CFWs)
cfw_positions = [(50, 90), (100, 90), (150, 90)]  # Posição inicial dos CFWs
for x, y in cfw_positions:
    canvas.create_rectangle(x, y, x + 50, y + 120, fill="lightgray", outline="black")
    canvas.create_text(x + 25, y + 60, text="CFW", font=("Arial", 12, "bold"))

# Vazão CFW
FT_CFW_text = canvas.create_text(110, 235, text="vazao", font=("Arial", 12, "bold"), anchor="w", fill="cyan")

# Linha de Mistura
canvas.create_rectangle(30, 260, 500, 290, fill="lightgray", outline="black")

#Misturador 1
canvas.create_rectangle(250, 250, 330, 300, fill="gray", outline="black")
canvas.create_text(290, 275, text="110.102", font=("Arial", 10, "bold"))

# Misturador 2
canvas.create_rectangle(360, 250, 440, 300, fill="gray", outline="black")
canvas.create_text(400, 275, text="110.103", font=("Arial", 10, "bold"))

# Vazao FC103
FT_103_text = canvas.create_text(550, 290, text="vazao", font=("Arial", 12, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(FT_103_text, "<Button-1>", control)

# CT-103
canvas.create_rectangle(490, 305, 650, 335, fill="lightgray", outline="black")
canvas.create_text(570, 320, text="CT-103", font=("Arial", 10, "bold"))

# CT-104
canvas.create_rectangle(620, 350, 780, 380, fill="lightgray", outline="black")
canvas.create_text(700, 365, text="CT-104", font=("Arial", 10, "bold"))

# Vazao Entrada Tremonha
FT_InSH_text = canvas.create_text(800, 365, text="vazao", font=("Arial", 12, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(FT_InSH_text, "<Button-1>", lambda e: open_graphic(3))

# Tremonha
canvas.create_rectangle(780, 390, 860, 490, fill="gray", outline="black")
SH_text = canvas.create_text(820, 410, text="SH", font=("Arial", 12, "bold"), fill="white")
canvas.tag_bind(SH_text, "<Button-1>", control_level)

# Nivel SH
nivelSH_text = canvas.create_text(820, 450, text="84.6%", font=("Arial", 12, "bold"), fill="yellow")
canvas.tag_bind(nivelSH_text, "<Button-1>", lambda e: open_graphic(1))

# Vazao saida Tremonha
canvas.create_text(620, 470, text="SH", font=("Arial", 12, "bold"), anchor="w", fill="black")
FT_OutSH_text = canvas.create_text(615, 490, text="vazao", font=("Arial", 12, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(FT_OutSH_text, "<Button-1>", lambda e: open_graphic(4))

# Vazao total Linha
canvas.create_text(490, 470, text="SH + HL", font=("Arial", 12, "bold"), anchor="w", fill="black")
FT_OutTot_text = canvas.create_text(495, 490, text="vazao", font=("Arial", 12, "bold"), anchor="w", fill="cyan")

# Linha de Sinter
canvas.create_rectangle(370, 510, 810, 540, fill="lightgray", outline="black")

# Maquina Sinter
canvas.create_rectangle(270, 490, 370, 560, fill="lightgray", outline="black")
canvas.create_text(320, 525, text="MAQUINA \n SINTER", font=("Arial", 10, "bold"))

# Parâmetros (caixa visual)
canvas.create_rectangle(30, 320, 250, 640, fill="darkgray", outline="black")
canvas.create_text(150, 335, text="PARAMETROS", font=("Arial", 12, "bold"), fill="black")

# Velocidade
canvas.create_text(50, 360, text="Velocidade (m/min): ", font=("Arial", 10), anchor="w", fill="black")
vel_text = canvas.create_text(180, 360, text="0.00", font=("Arial", 10, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(vel_text, "<Button-1>", text_sel)

# Altura Cam
canvas.create_text(50, 390, text="Altura Cam (mm): ", font=("Arial", 10), anchor="w", fill="black")
high_text = canvas.create_text(180, 390, text="600", font=("Arial", 10, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(high_text, "<Button-1>", text_sel)

# Largura CT
canvas.create_text(50, 420, text="Largura CT (mm): ", font=("Arial", 10), anchor="w", fill="black")
width_text = canvas.create_text(180, 420, text="4.00", font=("Arial", 10, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(width_text, "<Button-1>", text_sel)

# Densidade
canvas.create_text(50, 450, text="Densidade (t/m³): ", font=("Arial", 10), anchor="w", fill="black")
density_text = canvas.create_text(180, 450, text="2.10", font=("Arial", 10, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(density_text, "<Button-1>", text_sel)

# Umidade
canvas.create_text(50, 480, text="Umidade (%): ", font=("Arial", 10), anchor="w", fill="black")
humidity_text = canvas.create_text(180, 480, text="8.00", font=("Arial", 10, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(humidity_text, "<Button-1>", text_sel)

# Capacidade da Tremonha
canvas.create_text(50, 510, text="Vol. SH (m³): ", font=("Arial", 10), anchor="w", fill="black")
volume_text = canvas.create_text(180, 510, text="40.0", font=("Arial", 10, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(volume_text, "<Button-1>", text_sel)

# Limite Minimo
canvas.create_text(50, 540, text="Lim. Min.(t/h): ", font=("Arial", 10), anchor="w", fill="black")
Lmin_text = canvas.create_text(180, 540, text="650.0", font=("Arial", 10, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(Lmin_text, "<Button-1>", text_sel)

# Ganho
canvas.create_text(50, 570, text="Ganho: ", font=("Arial", 10), anchor="w", fill="black")
ganho_text = canvas.create_text(180, 570, text="0.16", font=("Arial", 10, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(ganho_text, "<Button-1>", text_sel)

# Setpoint
canvas.create_text(50, 600, text="Setpoint: ", font=("Arial", 10), anchor="w", fill="black")
SP_text = canvas.create_text(180, 600, text="65.0", font=("Arial", 10, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(SP_text, "<Button-1>", text_sel)

# Histerese
canvas.create_text(50, 630, text="Histerese: ", font=("Arial", 10), anchor="w", fill="black")
histerese_text = canvas.create_text(180, 630, text="100.0", font=("Arial", 10, "bold"), anchor="w", fill="cyan")
canvas.tag_bind(histerese_text, "<Button-1>", text_sel)

# Botão liga e desliga Simulação
lig_des_button = canvas.create_rectangle(700, 90, 830, 120, fill="lightgreen", outline="black")
lig_des_text = canvas.create_text(765, 105, text="Ligar Simulação", font=("Arial", 10, "bold"))
canvas.tag_bind(lig_des_button, "<Button-1>", toggle_simulacao)
canvas.tag_bind(lig_des_text, "<Button-1>", toggle_simulacao)

# Botão importar dados
import_button = canvas.create_rectangle(700, 150, 830, 180, fill="blue", outline="black")
import_text = canvas.create_text(765, 165, text="Importar dados", font=("Arial", 10, "bold"))
canvas.tag_bind(import_button, "<Button-1>", import_txt)
canvas.tag_bind(import_text, "<Button-1>", import_txt)

#--------------------------------------------------------------------------
#                             Conteudo ABA 4
#--------------------------------------------------------------------------
ttk.Label(aba4, text="Interface PLC v1.0", font=("Arial", 14)).pack(pady=20)
ttk.Label(aba4, text="Criado por ").pack(pady=10)


# Criar uma thread para o loop de atualização
def event_loop1():
    """Inicia o loop de eventos do asyncio em uma thread separada."""
    asyncio.run(Simulacao())

def event_loop2():
    """Inicia o loop de eventos do asyncio em uma thread separada."""
    asyncio.run(vazao())


sim1_thread = threading.Thread(target=event_loop1, daemon=True)
sim2_thread = threading.Thread(target=event_loop2, daemon=True)

sim1_thread.start()
sim2_thread.start()

# Encerrar o programa de forma segura
def on_close():
    global rodando
    global FT_103
    global FT_CFW
    global FI_CFW
    global FT
    global FT_SINTER
    global nivelSH
    
    rodando = False
    
    try:
        with open("Vetor_FT103.csv", mode="w", newline="") as file1:
            # Escreve os valores separados por virgula
            writer = csv.writer(file1)
            writer.writerow(FT_103)
        
        with open("Vetor_FTCFW.csv", mode="w",  newline="") as file2:
            # Escreve os valores separados por virgula
            writer = csv.writer(file2)
            writer.writerow(FT_CFW)
        
        with open("FI_CFW.csv", mode="w",  newline="") as file3:
            # Escreve os valores separados por virgula
            writer = csv.writer(file3)
            writer.writerow([FI_CFW])

        with open("nivelSH.csv", mode="w",  newline="") as file4:
            # Escreve os valores separados por virgula
            writer = csv.writer(file4)
            writer.writerow([nivelSH])
        
        with open("Vetor_FT.csv", mode="w",  newline="") as file5:
            # Escreve os valores separados por virgula
            writer = csv.writer(file5)
            writer.writerow(FT)
        
        with open("Vetor_FTSINTER.csv", mode="w",  newline="") as file6:
            # Escreve os valores separados por virgula
            writer = csv.writer(file6)
            writer.writerow(FT_SINTER)
            
    except Exception as e:
        print(f"Erro ao exportar vetor: {e}")
    
    if client.get_connected():
        client.disconnect()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)


# Iniciar a interface gráfica
root.mainloop()
