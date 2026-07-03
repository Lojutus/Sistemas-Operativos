import time
import threading
import argparse
import sys
import types
import os
import importlib.util

def load_hospital_class(use_old: bool):
    """Carga y retorna la clase HospitalNaive (actual o ANTIGUO) según flag."""
    if use_old:
        base_dir = os.path.dirname(__file__)
        old_path = os.path.join(base_dir, 'SistemasOperativoProblematica ANTIGUO.py')
        spec = importlib.util.spec_from_file_location('hospital_old', old_path)
        if spec is None or spec.loader is None:
            raise ImportError(f'No se pudo cargar el módulo antiguo desde: {old_path}')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, 'HospitalNaive')
    # actual
    try:
        from SO.SistemasOperativoProblematica import HospitalNaive as H
        return H
    except ModuleNotFoundError:
        from SistemasOperativoProblematica import HospitalNaive as H
        return H


def snapshot(h):
    lock = getattr(h, 'mutex', None)
    got = False
    if lock is not None:
        try:
            got = lock.acquire(timeout=0.05)
        except Exception:
            got = False
    try:
        camas = list(h.camas_ocupadas)
        f0 = list(h.filas[0])
        f1 = list(h.filas[1])
    finally:
        if got:
            try:
                lock.release()
            except Exception:
                pass
    return camas, f0, f1


def run_observation(camas, duracion, HospitalClass):
    h = HospitalClass(camas=camas)

    # Suprimir spam de estado para observación
    def _noop(self):
        return None
    try:
        h.mostrar_estado = types.MethodType(_noop, h)
    except Exception:
        pass

    # Iniciar hilos disponibles según la implementación
    threads = []
    if hasattr(h, 'pacienteNuevo'):
        threads.append(threading.Thread(target=h.pacienteNuevo, daemon=True, name='llegadas-base'))
    if hasattr(h, 'liberarPaciente'):
        threads.append(threading.Thread(target=h.liberarPaciente, daemon=True, name='altas-base'))
    if hasattr(h, 'pasarTiempo'):
        threads.append(threading.Thread(target=h.pasarTiempo, daemon=True, name='tiempo-base'))
    for t in threads:
        t.start()

    start = time.perf_counter()
    end = start + duracion

    samples = 0
    max_camas = 0
    max_f0 = 0
    max_f1 = 0
    dup_camas_count = 0
    both_queues_count = 0
    bed_and_queue_count = 0

    while time.perf_counter() < end:
        camas_list, f0_list, f1_list = snapshot(h)
        samples += 1

        max_camas = max(max_camas, len(camas_list))
        max_f0 = max(max_f0, len(f0_list))
        max_f1 = max(max_f1, len(f1_list))

        ids_c = list(map(id, camas_list))
        if len(ids_c) != len(set(ids_c)):
            dup_camas_count += 1

        set0 = set(map(id, f0_list))
        set1 = set(map(id, f1_list))
        inter = set0 & set1
        if inter:
            both_queues_count += 1

        set_c = set(map(id, camas_list))
        if set_c & set0 or set_c & set1:
            bed_and_queue_count += 1

        time.sleep(0.2)

    # Snapshot final para reporte de estado al cierre
    camas_fin, f0_fin, f1_fin = snapshot(h)

    print(f"Resumen (camas={camas}, duracion={duracion:.1f}s):")
    print(f"  Max camas ocupadas: {max_camas}/{camas}")
    print(f"  Max cola P1: {max_f1}, Max cola P0: {max_f0}")
    print(f"  Final cola P1: {len(f1_fin)}, Final cola P0: {len(f0_fin)}")
    # Exit code 0 siempre: este script es observacional
    return 0


def main():
    parser = argparse.ArgumentParser(description='Observa ejecución hospitalaria con hilos base.')
    parser.add_argument('--modo', choices=['suite', 'single'], default='suite', help='Ejecutar batería de casos (suite) o un solo caso (single). Default: suite')
    parser.add_argument('--camas', type=int, default=5, help='Número de camas para modo single (default: 5)')
    parser.add_argument('--duracion', type=float, default=5.0, help='Duración en segundos para modo single (default: 5.0)')
    parser.add_argument('--camasSuite', type=str, default=' 1,2,3,4', help='Lista de camas (coma-separada) para modo suite (default: 1,2,3,4)')
    parser.add_argument('--duracionSuite', type=float, default=10.0, help='Duración en segundos por caso en modo suite (default: 5.0)')
    parser.add_argument('--antiguo', action='store_true', help='Usar implementación antigua (SistemasOperativoProblematica ANTIGUO.py)')
    args = parser.parse_args()

    HospitalClass = load_hospital_class(args.antiguo)

    if args.modo == 'single':
        code = run_observation(args.camas, args.duracion, HospitalClass)
        sys.exit(code)
    else:
        # Suite por defecto: múltiples valores de camas, mayor duración
        try:
            camas_vals = [int(x.strip()) for x in args.camasSuite.split(',') if x.strip()]
        except Exception:
            camas_vals = [1, 3, 5, 8]
        for c in camas_vals:
            run_observation(c, args.duracionSuite, HospitalClass)
            time.sleep(0.5)
        sys.exit(0)


if __name__ == '__main__':
    main()
