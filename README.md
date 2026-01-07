# Sistema de Consultas Geoespaciales con R-Tree 📍

Este proyecto implementa un **Sistema de Consultas Geoespaciales** utilizando una estructura de datos **R-Tree** (Árbol R) para la indexación eficiente de puntos de interés (POIs). La aplicación permite visualizar, generar y consultar datos espaciales a través de una interfaz gráfica interactiva.

---

## 🧐 ¿Qué es un R-Tree?

El **R-Tree** es una estructura de datos de acceso espacial jerárquica (similar a un B-Tree pero para dimensiones múltiples). Se utiliza para organizar objetos geométricos agrupándolos mediante el concepto de **MBR (Minimum Bounding Rectangle)** o Rectángulo Mínimo de Contorno.

### Conceptos Clave
*   **MBR (Rectángulo Mínimo):** Es el rectángulo más pequeño que encierra todos los elementos (puntos o rectángulos) hijos de un nodo.
*   **Nodos Hoja:** Contienen los datos reales (en este caso, puntos de interés con su nombre y categoría).
*   **Nodos Internos:** Contienen MBRs que envuelven a sus nodos hijos, permitiendo "podar" o ignorar ramas enteras del árbol durante una búsqueda si no intersectan con el área de consulta.

---

## 🚀 Características del Sistema

1.  **Generación de Datos Inteligente:**
    *   **Aleatoria:** Distribución uniforme de puntos en el mapa.
    *   **Clusters (Agrupamientos):** Simula la realidad urbana donde los puntos de interés suelen agruparse en centros específicos (ej. centros comerciales, distritos).

2.  **Consultas Geoespaciales:**
    *   **Consulta de Rango (Range Query):** Permite al usuario dibujar un rectángulo en el mapa y recuperar instantáneamente todos los puntos contenidos en esa área.
    *   **K-Vecinos Más Cercanos (K-NN):** Encuentra los `K` puntos más próximos a una ubicación seleccionada mediante un click.

3.  **Visualización en Tiempo Real:** Interfaz gráfica desarrollada con `tkinter` que muestra la distribución de los puntos (coloreados por categoría) y los resultados de las consultas.

4.  **Analizador de Rendimiento:** Mide y muestra el tiempo de inserción y de ejecución de cada consulta para demostrar la eficiencia del R-Tree en comparación con búsquedas secuenciales.

---

## 🛠️ Estructura del Código

El archivo principal `Proyecto.py` está organizado en 5 partes fundamentales:

1.  **Implementación del R-Tree:**
    *   `Point`: Clase que representa coordenadas (x, y) y metadatos.
    *   `Rectangle (MBR)`: Lógica de intersección, cálculo de área y expansión.
    *   `RTree`: Gestión de la raíz, inserción con manejo de overflow (Split) y algoritmos de búsqueda recursiva.
2.  **Generador de Datos:** Clase `DataGenerator` para crear datasets de prueba realistas.
3.  **Analizador de Rendimiento:** Herramientas para benchmark de tiempos de respuesta.
4.  **Interfaz Gráfica (GUI):** Implementación completa en `tkinter` con eventos de mouse y canvas interactivo.
5.  **Programa Principal:** Punto de entrada de la aplicación.

---

## 💻 Requisitos e Instalación

### Requisitos
*   Python 3.x
*   Biblioteca `tkinter` (incluida habitualmente en instalaciones estándar de Python).

### Ejecución
Para iniciar el sistema, simplemente ejecute:
```bash
python Proyecto.py
```

---

## 📖 Instrucciones de Uso

1.  **Cargar Datos:** Ingrese la cantidad de puntos y use los botones "Generar Aleatorio" o "Generar Clusters".
2.  **Realizar Consulta de Rango:**
    *   Seleccione "Rango" en el panel izquierdo.
    *   Mantenga presionado el botón izquierdo del mouse y arrastre para dibujar el rectángulo.
3.  **Realizar Consulta K-NN:**
    *   Seleccione "K-NN" y defina el valor de `K` (ej. 5).
    *   Haga click en cualquier parte del mapa.
4.  **Analizar Resultados:** Observe el panel derecho para ver las estadísticas de tiempo y el listado de puntos encontrados.

---

## 🎓 Aspectos Académicos (Solución)

Este sistema soluciona el problema de las consultas espaciales masivas evitando el recorrido lineal ($O(n)$). Gracias al R-Tree:
*   La búsqueda se reduce a un problema de **complejidad logarítmica** en la mayoría de los casos.
*   El uso de **MBRs** optimiza el filtrado espacial, descargando rápidamente áreas que no contienen resultados.
*   La implementación incluye una lógica de **Split** (división de nodos) que mantiene el árbol balanceado, asegurando un rendimiento estable incluso con miles de puntos.

---

## 👥 Autores
*   [Añadir nombre de autores]

---
*Este proyecto fue desarrollado para el curso de Estructura de Datos Avanzadas.*
