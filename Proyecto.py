"""
Sistema de Consultas Geoespaciales con R-Tree
Proyecto Final - Métodos de Acceso Espacial
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import math
import random
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional
import json

# ============================================================================
# PARTE 1: IMPLEMENTACIÓN DEL R-TREE
# ============================================================================

@dataclass
class Point:
    """Representa un punto de interés"""
    x: float
    y: float
    name: str
    category: str
    
    def distance_to(self, other: 'Point') -> float:
        """Calcula distancia euclidiana a otro punto"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

@dataclass
class Rectangle:
    """Representa un rectángulo (MBR - Minimum Bounding Rectangle)"""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    def area(self) -> float:
        """Calcula el área del rectángulo"""
        return (self.max_x - self.min_x) * (self.max_y - self.min_y)
    
    def contains_point(self, point: Point) -> bool:
        """Verifica si un punto está dentro del rectángulo"""
        return (self.min_x <= point.x <= self.max_x and 
                self.min_y <= point.y <= self.max_y)
    
    def intersects(self, other: 'Rectangle') -> bool:
        """Verifica si dos rectángulos se intersectan"""
        return not (other.max_x < self.min_x or other.min_x > self.max_x or
                other.max_y < self.min_y or other.min_y > self.max_y)
    
    def enlargement_needed(self, point: Point) -> float:
        """Calcula el incremento de área necesario para incluir un punto"""
        new_min_x = min(self.min_x, point.x)
        new_min_y = min(self.min_y, point.y)
        new_max_x = max(self.max_x, point.x)
        new_max_y = max(self.max_y, point.y)
        new_area = (new_max_x - new_min_x) * (new_max_y - new_min_y)
        return new_area - self.area()
    
    def expand_to_include(self, point: Point):
        """Expande el rectángulo para incluir un punto"""
        self.min_x = min(self.min_x, point.x)
        self.min_y = min(self.min_y, point.y)
        self.max_x = max(self.max_x, point.x)
        self.max_y = max(self.max_y, point.y)

class RTreeNode:
    """Nodo del R-Tree"""
    def __init__(self, is_leaf: bool = True, max_entries: int = 4):
        self.is_leaf = is_leaf
        self.max_entries = max_entries
        self.entries = []  # Lista de (Rectangle, Point/Node)
        self.mbr = None  # Minimum Bounding Rectangle
    
    def is_full(self) -> bool:
        """Verifica si el nodo está lleno"""
        return len(self.entries) >= self.max_entries
    
    def calculate_mbr(self):
        """Calcula el MBR del nodo basado en sus entradas"""
        if not self.entries:
            return None
        
        min_x = min(rect.min_x for rect, _ in self.entries)
        min_y = min(rect.min_y for rect, _ in self.entries)
        max_x = max(rect.max_x for rect, _ in self.entries)
        max_y = max(rect.max_y for rect, _ in self.entries)
        
        self.mbr = Rectangle(min_x, min_y, max_x, max_y)

class RTree:
    """Implementación del R-Tree para indexación espacial"""
    def __init__(self, max_entries: int = 4):
        self.max_entries = max_entries
        self.root = RTreeNode(is_leaf=True, max_entries=max_entries)
        self.size = 0
        self.height = 1
    
    def insert(self, point: Point):
        """Inserta un punto en el R-Tree"""
        rect = Rectangle(point.x, point.y, point.x, point.y)
        
        # Encontrar la hoja apropiada
        leaf = self._choose_leaf(self.root, rect)
        
        # Insertar en la hoja
        leaf.entries.append((rect, point))
        leaf.calculate_mbr()
        self.size += 1
        
        # Manejar overflow si es necesario
        if leaf.is_full() and len(leaf.entries) > self.max_entries:
            self._split_node(leaf)
    
    def _choose_leaf(self, node: RTreeNode, rect: Rectangle) -> RTreeNode:
        """Elige la hoja más apropiada para insertar un rectángulo"""
        if node.is_leaf:
            return node
        
        # Elegir la entrada que requiere menor expansión
        min_enlargement = float('inf')
        best_entry = None
        
        for entry_rect, child_node in node.entries:
            enlargement = entry_rect.enlargement_needed(
                Point(rect.min_x, rect.min_y, "", "")
            )
            if enlargement < min_enlargement:
                min_enlargement = enlargement
                best_entry = (entry_rect, child_node)
        
        # Expandir el MBR y continuar recursivamente
        entry_rect, child_node = best_entry
        entry_rect.expand_to_include(Point(rect.min_x, rect.min_y, "", ""))
        entry_rect.expand_to_include(Point(rect.max_x, rect.max_y, "", ""))
        
        return self._choose_leaf(child_node, rect)
    
    def _split_node(self, node: RTreeNode):
        """Divide un nodo cuando está lleno (algoritmo simplificado)"""
        # Implementación simple: dividir en dos grupos
        entries = node.entries
        mid = len(entries) // 2
        
        # Crear nuevo nodo
        new_node = RTreeNode(is_leaf=node.is_leaf, max_entries=self.max_entries)
        new_node.entries = entries[mid:]
        node.entries = entries[:mid]
        
        # Recalcular MBRs
        node.calculate_mbr()
        new_node.calculate_mbr()
        
        # Si es la raíz, crear nueva raíz
        if node == self.root:
            new_root = RTreeNode(is_leaf=False, max_entries=self.max_entries)
            new_root.entries = [
                (node.mbr, node),
                (new_node.mbr, new_node)
            ]
            new_root.calculate_mbr()
            self.root = new_root
            self.height += 1
    
    def range_query(self, query_rect: Rectangle) -> List[Point]:
        """Búsqueda de puntos dentro de un área rectangular"""
        results = []
        self._range_search(self.root, query_rect, results)
        return results
    
    def _range_search(self, node: RTreeNode, query_rect: Rectangle, results: List[Point]):
        """Búsqueda recursiva en rango"""
        for entry_rect, entry_data in node.entries:
            if not entry_rect.intersects(query_rect):
                continue
            
            if node.is_leaf:
                # Es una hoja, verificar si el punto está dentro
                point = entry_data
                if query_rect.contains_point(point):
                    results.append(point)
            else:
                # Es un nodo interno, continuar recursivamente
                self._range_search(entry_data, query_rect, results)
    
    def knn_query(self, query_point: Point, k: int) -> List[Tuple[Point, float]]:
        """K vecinos más cercanos"""
        # Algoritmo simple: explorar todo el árbol y ordenar por distancia
        all_points = []
        self._collect_all_points(self.root, all_points)
        
        # Calcular distancias
        distances = [(p, query_point.distance_to(p)) for p in all_points]
        
        # Ordenar y retornar los k más cercanos
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    def _collect_all_points(self, node: RTreeNode, points: List[Point]):
        """Recolecta todos los puntos del árbol"""
        for _, entry_data in node.entries:
            if node.is_leaf:
                points.append(entry_data)
            else:
                self._collect_all_points(entry_data, points)

# ============================================================================
# PARTE 2: GENERADOR DE DATOS DE PRUEBA
# ============================================================================

class DataGenerator:
    """Genera datos de puntos de interés para pruebas"""
    
    CATEGORIES = {
        "Restaurante": ["La Trattoria", "El Buen Sabor", "Sushi House", "Pizza Express", 
                    "Café Central", "Burger King", "El Rincón", "Comida Rápida"],
        "Hospital": ["Hospital Central", "Clínica San Juan", "Centro Médico", 
                    "Hospital del Norte", "Clínica Santa María"],
        "Escuela": ["Colegio Nacional", "Instituto Técnico", "Universidad", 
                "Escuela Primaria", "Liceo"],
        "Banco": ["Banco Nacional", "Banco Popular", "Caja de Ahorros", 
                "Banco Internacional"],
        "Supermercado": ["Supermercado Central", "Mini Market", "Hipermercado", 
                        "Tienda de Barrio"],
        "Parque": ["Parque Central", "Plaza Principal", "Parque Infantil", 
                "Área Verde"],
    }
    
    @staticmethod
    def generate_random_points(count: int, width: float = 1000, height: float = 1000) -> List[Point]:
        """Genera puntos aleatorios"""
        points = []
        for i in range(count):
            category = random.choice(list(DataGenerator.CATEGORIES.keys()))
            name_base = random.choice(DataGenerator.CATEGORIES[category])
            name = f"{name_base} #{i+1}"
            
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            
            points.append(Point(x, y, name, category))
        
        return points
    
    @staticmethod
    def generate_clustered_points(count: int, num_clusters: int = 5, 
                                width: float = 1000, height: float = 1000) -> List[Point]:
        """Genera puntos agrupados en clusters"""
        points = []
        cluster_centers = [(random.uniform(100, width-100), 
                        random.uniform(100, height-100)) 
                        for _ in range(num_clusters)]
        
        for i in range(count):
            # Elegir un cluster aleatorio
            cx, cy = random.choice(cluster_centers)
            
            # Generar punto cerca del centro del cluster
            angle = random.uniform(0, 2 * math.pi)
            distance = random.gauss(50, 30)  # Distribución normal
            
            x = cx + distance * math.cos(angle)
            y = cy + distance * math.sin(angle)
            
            # Asegurar que está dentro de los límites
            x = max(0, min(width, x))
            y = max(0, min(height, y))
            
            category = random.choice(list(DataGenerator.CATEGORIES.keys()))
            name_base = random.choice(DataGenerator.CATEGORIES[category])
            name = f"{name_base} #{i+1}"
            
            points.append(Point(x, y, name, category))
        
        return points

# ============================================================================
# PARTE 3: ANALIZADOR DE RENDIMIENTO
# ============================================================================

class PerformanceAnalyzer:
    """Analiza el rendimiento de las consultas"""
    
    @staticmethod
    def measure_insertion_time(points: List[Point], max_entries: int = 4) -> Tuple[float, RTree]:
        """Mide el tiempo de inserción"""
        rtree = RTree(max_entries=max_entries)
        
        start_time = time.time()
        for point in points:
            rtree.insert(point)
        end_time = time.time()
        
        return end_time - start_time, rtree
    
    @staticmethod
    def measure_range_query_time(rtree: RTree, query_rect: Rectangle) -> Tuple[float, List[Point]]:
        """Mide el tiempo de una consulta de rango"""
        start_time = time.time()
        results = rtree.range_query(query_rect)
        end_time = time.time()
        
        return end_time - start_time, results
    
    @staticmethod
    def measure_knn_query_time(rtree: RTree, query_point: Point, k: int) -> Tuple[float, List[Tuple[Point, float]]]:
        """Mide el tiempo de una consulta k-NN"""
        start_time = time.time()
        results = rtree.knn_query(query_point, k)
        end_time = time.time()
        
        return end_time - start_time, results

# ============================================================================
# PARTE 4: INTERFAZ GRÁFICA CON TKINTER
# ============================================================================

class GeoSpatialGUI:
    """Interfaz gráfica principal del sistema"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Consultas Geoespaciales - R-Tree")
        self.root.geometry("1400x900")
        
        # Variables
        self.rtree = None
        self.points = []
        self.canvas_width = 800
        self.canvas_height = 600
        self.scale_factor = 1.0
        
        # Query results
        self.query_results = []
        self.query_rect = None
        self.query_point = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        
        # Panel superior - Controles
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Generación de datos
        ttk.Label(control_frame, text="Generar Datos:", font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=5)
        
        ttk.Label(control_frame, text="Cantidad:").grid(row=0, column=1, padx=5)
        self.count_var = tk.StringVar(value="100")
        ttk.Entry(control_frame, textvariable=self.count_var, width=10).grid(row=0, column=2, padx=5)
        
        ttk.Button(control_frame, text="Generar Aleatorio", 
                command=self.generate_random_data).grid(row=0, column=3, padx=5)
        ttk.Button(control_frame, text="Generar Clusters", 
                command=self.generate_clustered_data).grid(row=0, column=4, padx=5)
        ttk.Button(control_frame, text="Limpiar", 
                command=self.clear_data).grid(row=0, column=5, padx=5)
        
        # Panel izquierdo - Mapa
        left_frame = ttk.Frame(self.root, padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(left_frame, text="Mapa Interactivo", font=('Arial', 12, 'bold')).pack()
        
        # Canvas para el mapa
        self.canvas = tk.Canvas(left_frame, width=self.canvas_width, height=self.canvas_height, 
                            bg='white', cursor='cross')
        self.canvas.pack(pady=10)
        
        # Bind eventos del mouse
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        
        # Estado del dibujo
        self.drawing_rect = False
        self.rect_start = None
        self.current_rect_id = None
        
        # Controles de consulta
        query_frame = ttk.LabelFrame(left_frame, text="Consultas", padding="10")
        query_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(query_frame, text="Tipo de consulta:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.query_type_var = tk.StringVar(value="range")
        ttk.Radiobutton(query_frame, text="Rango (dibuje rectángulo)", 
                    variable=self.query_type_var, value="range").grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5)
        ttk.Radiobutton(query_frame, text="K-NN (click en punto)", 
                    variable=self.query_type_var, value="knn").grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5)
        
        ttk.Label(query_frame, text="K (vecinos):").grid(row=3, column=0, padx=5, sticky=tk.W)
        self.k_var = tk.StringVar(value="5")
        ttk.Entry(query_frame, textvariable=self.k_var, width=10).grid(row=3, column=1, padx=5, sticky=tk.W)
        
        ttk.Button(query_frame, text="Limpiar Consulta", 
                command=self.clear_query).grid(row=4, column=0, columnspan=2, pady=10)
        
        # Panel derecho - Resultados
        right_frame = ttk.Frame(self.root, padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(right_frame, text="Resultados y Estadísticas", 
                font=('Arial', 12, 'bold')).pack()
        
        # Área de texto para resultados
        self.results_text = scrolledtext.ScrolledText(right_frame, width=60, height=30, 
                                                    wrap=tk.WORD, font=('Courier', 9))
        self.results_text.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Estadísticas
        stats_frame = ttk.LabelFrame(right_frame, text="Estadísticas del R-Tree", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.stats_label = ttk.Label(stats_frame, text="No hay datos cargados", 
                                    font=('Arial', 9))
        self.stats_label.pack()
        
        # Configurar pesos de grid
        self.root.columnconfigure(0, weight=2)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)
    
    def generate_random_data(self):
        """Genera y carga datos aleatorios"""
        try:
            count = int(self.count_var.get())
            if count <= 0 or count > 10000:
                messagebox.showerror("Error", "La cantidad debe estar entre 1 y 10000")
                return
            
            # Generar puntos
            self.points = DataGenerator.generate_random_points(count, self.canvas_width, self.canvas_height)
            
            # Construir R-Tree y medir tiempo
            insertion_time, self.rtree = PerformanceAnalyzer.measure_insertion_time(self.points)
            
            # Actualizar visualización
            self.draw_map()
            self.update_stats(insertion_time)
            
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"✓ Generados {count} puntos aleatorios\n")
            self.results_text.insert(tk.END, f"✓ R-Tree construido en {insertion_time:.4f} segundos\n")
            self.results_text.insert(tk.END, f"✓ Promedio: {insertion_time/count*1000:.4f} ms por punto\n\n")
            
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido")
    
    def generate_clustered_data(self):
        """Genera datos agrupados en clusters"""
        try:
            count = int(self.count_var.get())
            if count <= 0 or count > 10000:
                messagebox.showerror("Error", "La cantidad debe estar entre 1 y 10000")
                return
            
            # Generar puntos en clusters
            self.points = DataGenerator.generate_clustered_points(count, 5, 
                                                                self.canvas_width, self.canvas_height)
            
            # Construir R-Tree y medir tiempo
            insertion_time, self.rtree = PerformanceAnalyzer.measure_insertion_time(self.points)
            
            # Actualizar visualización
            self.draw_map()
            self.update_stats(insertion_time)
            
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"✓ Generados {count} puntos en clusters\n")
            self.results_text.insert(tk.END, f"✓ R-Tree construido en {insertion_time:.4f} segundos\n")
            self.results_text.insert(tk.END, f"✓ Promedio: {insertion_time/count*1000:.4f} ms por punto\n\n")
            
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido")
    
    def clear_data(self):
        """Limpia todos los datos"""
        self.rtree = None
        self.points = []
        self.query_results = []
        self.canvas.delete('all')
        self.results_text.delete(1.0, tk.END)
        self.stats_label.config(text="No hay datos cargados")
    
    def draw_map(self):
        """Dibuja todos los puntos en el mapa"""
        self.canvas.delete('all')
        
        # Colores por categoría
        colors = {
            "Restaurante": "#FF6B6B",
            "Hospital": "#4ECDC4",
            "Escuela": "#45B7D1",
            "Banco": "#FFA07A",
            "Supermercado": "#98D8C8",
            "Parque": "#6BCF7F",
        }
        
        # Dibujar todos los puntos
        for point in self.points:
            color = colors.get(point.category, "#999999")
            self.canvas.create_oval(point.x-3, point.y-3, point.x+3, point.y+3, 
                                fill=color, outline='black', width=1, tags='point')
        
        # Redibujar consulta si existe
        if self.query_results:
            self.highlight_results()
    
    def on_canvas_click(self, event):
        """Maneja click en el canvas"""
        if not self.rtree:
            messagebox.showwarning("Advertencia", "Primero genere datos")
            return
        
        query_type = self.query_type_var.get()
        
        if query_type == "range":
            # Iniciar dibujo de rectángulo
            self.drawing_rect = True
            self.rect_start = (event.x, event.y)
            self.current_rect_id = self.canvas.create_rectangle(
                event.x, event.y, event.x, event.y, 
                outline='blue', width=2, dash=(5, 5), tags='query_rect'
            )
        elif query_type == "knn":
            # Consulta K-NN
            self.perform_knn_query(event.x, event.y)
    
    def on_canvas_drag(self, event):
        """Maneja arrastre del mouse"""
        if self.drawing_rect and self.current_rect_id:
            self.canvas.coords(self.current_rect_id, 
                            self.rect_start[0], self.rect_start[1], 
                            event.x, event.y)
    
    def on_canvas_release(self, event):
        """Maneja liberación del mouse"""
        if self.drawing_rect:
            self.drawing_rect = False
            # Realizar consulta de rango
            self.perform_range_query(self.rect_start[0], self.rect_start[1], 
                                    event.x, event.y)
    
    def perform_range_query(self, x1, y1, x2, y2):
        """Ejecuta consulta de rango"""
        # Crear rectángulo de consulta
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        query_rect = Rectangle(min_x, min_y, max_x, max_y)
        
        # Medir tiempo y ejecutar consulta
        query_time, results = PerformanceAnalyzer.measure_range_query_time(self.rtree, query_rect)
        
        self.query_results = results
        self.query_rect = query_rect
        
        # Mostrar resultados
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "═══ CONSULTA DE RANGO ═══\n\n")
        self.results_text.insert(tk.END, f"Área consultada: ({min_x:.1f}, {min_y:.1f}) a ({max_x:.1f}, {max_y:.1f})\n")
        self.results_text.insert(tk.END, f"Tiempo de consulta: {query_time*1000:.4f} ms\n")
        self.results_text.insert(tk.END, f"Puntos encontrados: {len(results)}\n\n")
        
        # Agrupar por categoría
        by_category = {}
        for point in results:
            if point.category not in by_category:
                by_category[point.category] = []
            by_category[point.category].append(point)
        
        self.results_text.insert(tk.END, "─── Puntos por Categoría ───\n")
        for category, points in sorted(by_category.items()):
            self.results_text.insert(tk.END, f"\n{category} ({len(points)}):\n")
            for point in points[:10]:  # Mostrar máximo 10
                self.results_text.insert(tk.END, f"  • {point.name} ({point.x:.1f}, {point.y:.1f})\n")
            if len(points) > 10:
                self.results_text.insert(tk.END, f"  ... y {len(points)-10} más\n")
        
        # Resaltar en mapa
        self.highlight_results()
    
    def perform_knn_query(self, x, y):
        """Ejecuta consulta K-NN"""
        try:
            k = int(self.k_var.get())
            if k <= 0:
                messagebox.showerror("Error", "K debe ser mayor que 0")
                return
        except ValueError:
            messagebox.showerror("Error", "Ingrese un valor válido para K")
            return
        
        query_point = Point(x, y, "Query Point", "")
        
        # Medir tiempo y ejecutar consulta
        query_time, results = PerformanceAnalyzer.measure_knn_query_time(self.rtree, query_point, k)
        
        self.query_point = query_point
        self.query_results = [point for point, _ in results]
        
        # Mostrar resultados
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "═══ CONSULTA K-NN ═══\n\n")
        self.results_text.insert(tk.END, f"Punto de consulta: ({x:.1f}, {y:.1f})\n")
        self.results_text.insert(tk.END, f"K vecinos: {k}\n")
        self.results_text.insert(tk.END, f"Tiempo de consulta: {query_time*1000:.4f} ms\n\n")
        
        self.results_text.insert(tk.END, "─── Vecinos Más Cercanos ───\n")
        for i, (point, distance) in enumerate(results, 1):
            self.results_text.insert(tk.END, 
                f"{i}. {point.name} [{point.category}]\n")
            self.results_text.insert(tk.END, 
                f"   Posición: ({point.x:.1f}, {point.y:.1f}) - Distancia: {distance:.2f}\n\n")
        
        # Resaltar en mapa
        self.highlight_results()
        
        # Dibujar punto de consulta
        self.canvas.create_oval(x-5, y-5, x+5, y+5, 
                            fill='red', outline='darkred', width=2, tags='query_point')
        
        # Dibujar líneas a vecinos
        for point, distance in results:
            self.canvas.create_line(x, y, point.x, point.y, 
                                fill='red', dash=(3, 3), tags='knn_line')
    
    def highlight_results(self):
        """Resalta los resultados de la consulta en el mapa"""
        # Limpiar highlights previos
        self.canvas.delete('highlight')
        self.canvas.delete('query_rect')
        self.canvas.delete('query_point')
        self.canvas.delete('knn_line')
        
        # Redibujar rectángulo de consulta si existe
        if self.query_rect:
            self.canvas.create_rectangle(
                self.query_rect.min_x, self.query_rect.min_y,
                self.query_rect.max_x, self.query_rect.max_y,
                outline='blue', width=2, dash=(5, 5), tags='query_rect'
            )
        
        # Resaltar puntos encontrados
        for point in self.query_results:
            self.canvas.create_oval(point.x-5, point.y-5, point.x+5, point.y+5, 
                                fill='yellow', outline='orange', width=2, 
                                tags='highlight')
    
    def clear_query(self):
        """Limpia la consulta actual"""
        self.query_results = []
        self.query_rect = None
        self.query_point = None
        self.canvas.delete('highlight')
        self.canvas.delete('query_rect')
        self.canvas.delete('query_point')
        self.canvas.delete('knn_line')
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Consulta limpiada. Dibuje un rectángulo o haga click para nueva consulta.\n")
    
    def update_stats(self, insertion_time):
        """Actualiza estadísticas del R-Tree"""
        if not self.rtree:
            return
        
        stats_text = f"""
Puntos indexados: {self.rtree.size}
Altura del árbol: {self.rtree.height}
Tiempo de construcción: {insertion_time:.4f} s
Tiempo promedio por inserción: {insertion_time/self.rtree.size*1000:.4f} ms
Máx. entradas por nodo: {self.rtree.max_entries}
        """
        self.stats_label.config(text=stats_text)


# ============================================================================
# PARTE 5: PROGRAMA PRINCIPAL
# ============================================================================

def main():
    """Función principal"""
    root = tk.Tk()
    app = GeoSpatialGUI(root)
    
    # Mensaje de bienvenida
    app.results_text.insert(tk.END, "═══════════════════════════════════════════════════\n")
    app.results_text.insert(tk.END, "  SISTEMA DE CONSULTAS GEOESPACIALES CON R-TREE\n")
    app.results_text.insert(tk.END, "═══════════════════════════════════════════════════\n\n")
    app.results_text.insert(tk.END, "Instrucciones:\n\n")
    app.results_text.insert(tk.END, "1. Genere datos usando los botones superiores\n")
    app.results_text.insert(tk.END, "2. Seleccione tipo de consulta:\n")
    app.results_text.insert(tk.END, "   • RANGO: Dibuje un rectángulo en el mapa\n")
    app.results_text.insert(tk.END, "   • K-NN: Haga click en un punto del mapa\n")
    app.results_text.insert(tk.END, "3. Los resultados aparecerán aquí\n\n")
    app.results_text.insert(tk.END, "Categorías de puntos:\n")
    app.results_text.insert(tk.END, "  🔴 Restaurante  🔵 Hospital  🟢 Escuela\n")
    app.results_text.insert(tk.END, "  🟠 Banco  🟣 Supermercado  🟢 Parque\n\n")
    
    root.mainloop()


if __name__ == "__main__":
    main()