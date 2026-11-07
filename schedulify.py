import streamlit as st
import pandas as pd
from collections import deque

# =========================
# KONFIGURASI APLIKASI
# =========================

st.set_page_config(
    page_title="Schedulify",
    layout="wide"
)

st.title("Schedulify")
st.subheader("CPU Scheduling Simulator")
st.write("Simulasi algoritma SJF dan Multilevel Feedback Queue")


# =========================
# DATA PROSES
# =========================

if "processes" not in st.session_state:
    st.session_state.processes = []


# =========================
# PERHITUNGAN WAKTU
# =========================

def calculate_process(p, start, completion):
    turnaround = completion - p["Arrival"]
    waiting = turnaround - p["Burst"]
    response = start - p["Arrival"]

    return {
        "Process": p["Process"],
        "Arrival": p["Arrival"],
        "Burst": p["Burst"],
        "Start": start,
        "Completion": completion,
        "Turnaround": turnaround,
        "Waiting": waiting,
        "Response": response
    }


# =========================
# ALGORITMA SJF
# NON-PREEMPTIVE
# =========================

def sjf(processes):

    if not processes:
        return [], []

    time = 0
    completed = set()
    results = []
    gantt = []

    while len(completed) < len(processes):

        ready = [
            p for p in processes
            if p["Process"] not in completed
            and p["Arrival"] <= time
        ]

        # Jika belum ada proses yang datang
        if not ready:

            next_arrival = min(
                p["Arrival"] for p in processes
                if p["Process"] not in completed
            )

            if time < next_arrival:
                gantt.append(
                    ("Idle", time, next_arrival)
                )

            time = next_arrival
            continue

        # Pilih Burst Time paling kecil
        ready.sort(
            key=lambda p: (
                p["Burst"],
                p["Arrival"]
            )
        )

        p = ready[0]

        start = time
        completion = start + p["Burst"]

        results.append(
            calculate_process(
                p,
                start,
                completion
            )
        )

        gantt.append(
            (p["Process"], start, completion)
        )

        time = completion
        completed.add(p["Process"])

    return results, gantt


# =========================
# ALGORITMA MLFQ
# =========================

def mlfq(processes):

    if not processes:
        return [], []

    # Tiga antrean
    queues = [
        deque(),
        deque(),
        deque()
    ]

    # Quantum Queue 1 dan Queue 2
    quantum = [2, 4]

    # Sisa Burst Time
    remaining = {
        p["Process"]: p["Burst"]
        for p in processes
    }

    first_start = {}
    completion = {}

    # Quantum yang sudah digunakan
    quantum_used = {
        p["Process"]: 0
        for p in processes
    }

    arrived = set()
    gantt = []

    time = 0
    running = None

    while len(completion) < len(processes):

        # 1. Masukkan proses yang sudah datang
        for p in processes:

            pid = p["Process"]

            if (
                p["Arrival"] <= time
                and pid not in arrived
            ):

                queues[0].append(pid)
                arrived.add(pid)
                quantum_used[pid] = 0

        # 2. Cari antrean dengan prioritas tertinggi
        highest_queue = next(
            (
                i for i, q in enumerate(queues)
                if q
            ),
            None
        )

        # 3. Pemeriksaan preemption
        if running is not None:

            pid, current_level = running

            if (
                highest_queue is not None
                and highest_queue < current_level
            ):

                # Kembalikan proses ke depan antrean
                queues[current_level].appendleft(pid)

                # Sisa quantum tetap dipertahankan
                running = None

        # 4. Pilih proses jika CPU kosong
        if running is None:

            level = next(
                (
                    i for i, q in enumerate(queues)
                    if q
                ),
                None
            )

            # Jika tidak ada proses siap
            if level is None:

                future_arrivals = [
                    p["Arrival"]
                    for p in processes
                    if p["Process"] not in arrived
                ]

                if not future_arrivals:
                    break

                next_arrival = min(future_arrivals)

                if time < next_arrival:

                    if (
                        gantt
                        and gantt[-1][0] == "Idle"
                        and gantt[-1][2] == time
                    ):

                        old = gantt.pop()

                        gantt.append(
                            (
                                "Idle",
                                old[1],
                                next_arrival
                            )
                        )

                    else:

                        gantt.append(
                            (
                                "Idle",
                                time,
                                next_arrival
                            )
                        )

                time = next_arrival
                continue

            pid = queues[level].popleft()

            running = (pid, level)

        pid, level = running

        # 5. Catat waktu pertama proses berjalan
        if pid not in first_start:

            first_start[pid] = time

        # 6. Jalankan proses selama satu satuan waktu
        start = time

        time += 1

        remaining[pid] -= 1

        if level < 2:

            quantum_used[pid] += 1

        # 7. Buat Gantt Chart
        if (
            gantt
            and gantt[-1][0] == pid
            and gantt[-1][2] == start
        ):

            old = gantt.pop()

            gantt.append(
                (
                    pid,
                    old[1],
                    time
                )
            )

        else:

            gantt.append(
                (
                    pid,
                    start,
                    time
                )
            )

        # 8. Evaluasi kondisi proses
        if remaining[pid] == 0:

            completion[pid] = time
            running = None

        # Quantum habis
        elif (
            level < 2
            and quantum_used[pid] >= quantum[level]
        ):

            # Turunkan ke antrean berikutnya
            next_level = level + 1

            queues[next_level].append(pid)

            quantum_used[pid] = 0
            running = None

        # Queue 3 menggunakan FCFS
        # sampai proses selesai atau di-preempt

    # 9. Hitung hasil akhir
    results = []

    for p in processes:

        pid = p["Process"]

        results.append(
            calculate_process(
                p,
                first_start[pid],
                completion[pid]
            )
        )

    return results, gantt


# =========================
# FORM INPUT PROSES
# =========================

st.header("Input Proses")

with st.form("process_form"):

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        pid = st.text_input(
            "Nama Proses",
            placeholder="P1"
        )

    with col2:

        arrival = st.number_input(
            "Arrival Time",
            min_value=0,
            step=1
        )

    with col3:

        burst = st.number_input(
            "Burst Time",
            min_value=1,
            step=1
        )

    with col4:

        st.write(" ")
        st.write(" ")

        add = st.form_submit_button(
            "Tambah Proses"
        )

    if add:

        clean_pid = pid.strip()

        if not clean_pid:

            st.error(
                "Nama proses tidak boleh kosong."
            )

        elif any(
            p["Process"].lower() == clean_pid.lower()
            for p in st.session_state.processes
        ):

            st.error(
                "Nama proses sudah digunakan."
            )

        else:

            st.session_state.processes.append({

                "Process": clean_pid,
                "Arrival": int(arrival),
                "Burst": int(burst)

            })

            st.session_state.pop(
                "results",
                None
            )

            st.session_state.pop(
                "gantt",
                None
            )

            st.success(
                "Proses berhasil ditambahkan!"
            )


# =========================
# TAMPILKAN DATA PROSES
# =========================

st.header("Daftar Proses")

if st.session_state.processes:

    st.dataframe(
        pd.DataFrame(
            st.session_state.processes
        ),
        use_container_width=True
    )

    if st.button("Hapus Semua Proses"):

        st.session_state.processes = []

        st.session_state.pop(
            "results",
            None
        )

        st.session_state.pop(
            "gantt",
            None
        )

        st.rerun()

else:

    st.info(
        "Belum ada proses yang dimasukkan."
    )


# =========================
# PILIH ALGORITMA
# =========================

st.divider()

st.header("Simulasi Scheduling")

algorithm = st.selectbox(
    "Pilih Algoritma",
    ["SJF", "MLFQ"]
)

if algorithm == "SJF":

    st.info(
        "SJF: Non-Preemptive Shortest Job First."
    )

if algorithm == "MLFQ":

    st.info(
        "Queue 1: Quantum 2 | "
        "Queue 2: Quantum 4 | "
        "Queue 3: FCFS"
    )


if st.button("Jalankan Simulasi"):

    if not st.session_state.processes:

        st.warning(
            "Masukkan proses terlebih dahulu."
        )

    else:

        if algorithm == "SJF":

            results, gantt = sjf(
                st.session_state.processes
            )

        else:

            results, gantt = mlfq(
                st.session_state.processes
            )

        st.session_state.results = results
        st.session_state.gantt = gantt

        st.session_state.last_algorithm = algorithm


# =========================
# HASIL SIMULASI
# =========================

if (
    "results" in st.session_state
    and "gantt" in st.session_state
    and st.session_state.processes
):

    st.divider()

    st.header("Gantt Chart")

    gantt_data = []

    for process, start, end in st.session_state.gantt:

        gantt_data.append({

            "Process": process,
            "Mulai": start,
            "Selesai": end

        })

    st.dataframe(
        pd.DataFrame(gantt_data),
        use_container_width=True
    )

    st.header("Tabel Hasil Scheduling")

    df = pd.DataFrame(
        st.session_state.results
    )

    st.dataframe(
        df,
        use_container_width=True
    )

    # Rata-rata waktu
    st.header("Rata-rata Waktu")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Average Turnaround Time",
            f"{df['Turnaround'].mean():.2f}"
        )

    with col2:

        st.metric(
            "Average Waiting Time",
            f"{df['Waiting'].mean():.2f}"
        )

    with col3:

        st.metric(
            "Average Response Time",
            f"{df['Response'].mean():.2f}"
        )


# =========================
# RUMUS PERHITUNGAN
# =========================

st.divider()

st.header("Rumus Perhitungan")

st.write(
    "**Turnaround Time** = "
    "Completion Time - Arrival Time"
)

st.write(
    "**Waiting Time** = "
    "Turnaround Time - Burst Time"
)

st.write(
    "**Response Time** = "
    "First Start Time - Arrival Time"
)


# =========================
# ANGGOTA KELOMPOK
# =========================

st.divider()

st.header("Anggota Kelompok")

anggota = pd.DataFrame({

    "No": [1, 2, 3, 4, 5],

    "NIM": [
        "2501020002",
        "2501020006",
        "2501020032",
        "2501020046",
        "2501020049"
    ],

    "Nama Anggota": [
        "Mohd Athalla Pria Riardy",
        "Muhammad Iqbal",
        "Mohammad Alfin Faris Adz Dzikkri",
        "Mohammad Pandu Wirahman",
        "Fery Febrian"
    ]

})

st.dataframe(
    anggota,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "kelompok 5: SJF, Multilevel Feedback Queue"
)