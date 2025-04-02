from flask import Flask, render_template, request
import plotly.graph_objects as go
from collections import deque
import random
import webbrowser
from threading import Timer
import copy

app = Flask(__name__)

class Process:
    def __init__(self, pid, arrival, burst, priority):
        self.id = pid
        self.arrival_time = arrival
        self.burst_time = burst
        self.priority = priority

def fcfs(processes):
    if not processes:
        return []
    timeline = []
    time = 0
    for p in sorted(processes, key=lambda x: x.arrival_time):
        if time < p.arrival_time:
            time = p.arrival_time
        timeline.append((time, p.burst_time, p.id))
        time += p.burst_time
    return timeline

def sjf(processes):
    if not processes:
        return []
    timeline = []
    time = 0
    ready = []
    processes = sorted(processes, key=lambda x: x.arrival_time)
    completed = []
    i = 0
    while len(completed) < len(processes):
        while i < len(processes) and processes[i].arrival_time <= time:
            ready.append(processes[i])
            i += 1
        if ready:
            ready.sort(key=lambda x: x.burst_time)
            p = ready.pop(0)
            timeline.append((time, p.burst_time, p.id))
            time += p.burst_time
            completed.append(p)
        else:
            time += 1
    return timeline

def round_robin(processes, quantum):
    if not processes or quantum <= 0:
        return []
    time = 0
    q = deque()
    timeline = []
    remaining = {p.id: p.burst_time for p in processes}
    completed = set()
    processes = sorted(processes, key=lambda x: x.arrival_time)
    i = 0
    queue_set = set()

    while len(completed) < len(processes):
        while i < len(processes) and processes[i].arrival_time <= time:
            if processes[i].id not in queue_set:
                q.append(processes[i])
                queue_set.add(processes[i].id)
            i += 1

        if q:
            p = q.popleft()
            queue_set.discard(p.id)
            exec_time = min(quantum, remaining[p.id])
            timeline.append((time, exec_time, p.id))
            time += exec_time
            remaining[p.id] -= exec_time

            while i < len(processes) and processes[i].arrival_time <= time:
                if processes[i].id not in queue_set and processes[i].id not in completed:
                    q.append(processes[i])
                    queue_set.add(processes[i].id)
                i += 1

            if remaining[p.id] > 0:
                q.append(p)
                queue_set.add(p.id)
            else:
                completed.add(p.id)
        else:
            time += 1
    return timeline

def priority_scheduling(processes):
    if not processes:
        return []
    timeline = []
    time = 0
    ready = []
    completed = []
    processes = sorted(processes, key=lambda x: x.arrival_time)
    i = 0

    while len(completed) < len(processes):
        while i < len(processes) and processes[i].arrival_time <= time:
            ready.append(processes[i])
            i += 1
        if ready:
            ready.sort(key=lambda x: x.priority)
            p = ready.pop(0)
            timeline.append((time, p.burst_time, p.id))
            time += p.burst_time
            completed.append(p)
        else:
            time += 1
    return timeline

def create_gantt_chart(timeline, title):
    if not timeline:
        return "<div>No processes in this timeline</div>"
    
    fig = go.Figure()
    process_colors = {}
    unique_processes = list(set([p[2] for p in timeline]))
    
    for process in unique_processes:
        process_colors[process] = f"rgb({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)})"
    
    for start, duration, process in timeline:
        fig.add_trace(go.Bar(
            x=[duration],
            y=[process],
            base=[start],
            orientation='h',
            marker_color=process_colors[process],
            name=process,
            hoverinfo='text',
            hovertext=f'Process: {process}<br>Start: {start}<br>Duration: {duration}'
        ))
    
    fig.update_layout(
        title=title,
        barmode='stack',
        xaxis_title='Time',
        yaxis_title='Processes',
        showlegend=False,
        height=400,
        margin=dict(l=100, r=100, t=100, b=100)
    )
    
    return fig.to_html(full_html=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            n = int(request.form['process_count'])
            quantum = int(request.form['quantum'])
            
            processes = []
            for i in range(n):
                pid = f"P{i+1}"
                arrival = int(request.form.get(f'arrival_{i}', 0))
                burst = int(request.form.get(f'burst_{i}', 1))
                priority = int(request.form.get(f'priority_{i}', 1))
                processes.append(Process(pid, arrival, burst, priority))
            
            algorithms = {
                "FCFS": fcfs(copy.deepcopy(processes)),
                "SJF": sjf(copy.deepcopy(processes)),
                "Round Robin": round_robin(copy.deepcopy(processes), quantum),
                "Priority": priority_scheduling(copy.deepcopy(processes))
            }
            
            charts = {}
            for name, timeline in algorithms.items():
                charts[name] = create_gantt_chart(timeline, f"{name} Scheduling")
            
            return render_template('results.html', charts=charts)
        
        except Exception as e:
            return f"Error processing input: {str(e)}"
    
    return render_template('index.html')

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(debug=True)
    