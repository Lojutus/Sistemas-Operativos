import random
import collections
import time
import threading


class Paciente:
    def __init__(self, prioridad, tiempoEspera=0, hospital=None):
        self.prioridad = prioridad  # 0 = baja, 1 = alta
        self.esperaMax = tiempoEspera
        self.hospital = hospital
        # tiempo que ha pasado desde que llegó al hospital
        hilo_espera = threading.Thread(target=self.esperar, daemon=True)
        hilo_espera.start()
    def __repr__(self):
        return f"P(prio={self.prioridad}, espera={self.esperaMax})"
   
    def esperar(self):
        """Simula el paso del tiempo de espera para el paciente."""
        while True:
            if self.esperaMax > 0:
                self.esperaMax -= 1
            else:
                if self.hospital is None:
                    break
                self.hospital.solicitarTransladoUrgente(self)
                break
            time.sleep(1)  # Simula el paso del tiempo (1 segundo por unidad de espera)
    def estaEsperandoDemasiado(self):
        """Verifica si el paciente ha estado esperando demasiado tiempo."""
        return self.esperaMax <= 0


class HospitalNaive:
    """Versión ingenua: el flujo de llegada depende solo de la prioridad,
    por lo que pacientes de alta prioridad tienden a acaparar las camas.
    """
    def __init__(self, camas):
        self.N = camas
        # filas separadas por prioridad: 1(alta),0(baja)
        self.filas = {1: collections.deque(), 0: collections.deque()}
        self.camas_ocupadas = []  # lista de pacientes en cama
        self.mutex = threading.Lock()  # Mutex para proteger el acceso a las filas y camas
        

    def llegada_aleatoria_por_prioridad(self):
        """Genera llegada infinita controlada: prioridad elegida aleatoriamente
        pero con sesgo hacia prioridades altas para evidenciar la problemática.
        """
        r = random.random()
        if r < 0.5:
            pr = 1
        elif r < 1.0:
            pr = 0
        else:
            pr = 0
        espera = random.randint(5, 20)
        if pr == 1:
            espera = 0
        p = Paciente( pr, espera, hospital=self)
        self.filas[pr].append(p)

    def asignar_camas(self):
        """Asignación : siempre servir a la fila de mayor prioridad
        disponible hasta llenar camas.
        """
        while len(self.camas_ocupadas) < self.N:
            elegido = None
            for pr in (1, 0):
                if self.filas[pr]:
                    elegido = self.filas[pr].popleft()
                    break
            if elegido is None:
                break  # no hay pacientes
            self.camas_ocupadas.append(elegido)

    
    def eliminar_paciente_baja_prioridad(self):
        """Busca el primer paciente de prioridad 0 en las camas y lo elimina."""
        for paciente in self.camas_ocupadas:
            if paciente.prioridad == 0:
                self.camas_ocupadas.remove(paciente)
                return True  # Se encontró y eliminó con éxito
        
        return False  # No había ningún paciente con prioridad 0
    def liberar_aleatoria(self):
        """Simula egresos aleatorios de camas para liberar espacio.
        """
        if not self.camas_ocupadas:
            return
        else:
            if(not self.eliminar_paciente_baja_prioridad()):
                self.camas_ocupadas.pop()
    def estado(self):
        return {
            'camas_ocupadas': list(self.camas_ocupadas),
            'filas': {k: list(v) for k, v in self.filas.items()}
        }
    def mostrar_estado(self):
        
        print("\n--- ESTADO DEL HOSPITAL ---")
        print(f"Fila Alta Prioridad (1): {len(list(self.filas[1]))} pacientes")
        print(f"Fila Baja Prioridad (0): {len(list(self.filas[0]))} pacientes")
        print("---------------------------")

    def pacienteNuevo(self):
        """Simula la llegada de un nuevo paciente.
        """
        while True:
            self.llegada_aleatoria_por_prioridad()
            self.asignar_camas()
            self.mostrar_estado()
            time.sleep(1)  # Simula tiempo entre llegadas

    def liberarPaciente(self):
        """Simula la liberación de un paciente aleatorio.
        """
        while True:
            self.liberar_aleatoria()
            self.mostrar_estado()
            time.sleep(2)  # Simula tiempo entre liberaciones
    def solicitarTransladoUrgente(self , paciente):
        # función para aumentar la prioridad de un paciente de baja prioridad a alta prioridad
        
        with self.mutex:
        
            if paciente in self.filas[1]:
                return  # Ya está en la fila de alta prioridad, no hacer nada
            if paciente in self.filas[0]:
                self.filas[1].append(paciente)
                self.filas[0].remove(paciente)
               

    def pasarTiempo(self):
        """Simula el paso del tiempo para todos los pacientes bajos"""
        while True:
            
            time.sleep(2)  # Simula el paso del tiempo
        
if __name__ == '__main__':
    # Ejecutar simulación sencilla (sin harness; el harness está en un script aparte)
    hospital = HospitalNaive(camas=5)

    hilo = threading.Thread(target=hospital.pacienteNuevo, daemon=True)
    hilo.start()

    hilo2 = threading.Thread(target=hospital.liberarPaciente, daemon=True)
    hilo2.start()

    
    try:
        while True:
            time.sleep(1)  # Mantiene el programa principal corriendo
    except KeyboardInterrupt:
        print("\n[Principal] Simulación finalizada.")

        #FINAL