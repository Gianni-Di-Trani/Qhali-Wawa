from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.uix.widget import Widget
import os
import cv2
import numpy as np
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.uix.togglebutton import ToggleButton
import gspread
from google.oauth2 import service_account
from kivy.utils import platform
from pynput.mouse import Listener as MouseListener
from flask import Flask, Response
import threading

# Pantalla de inicio de sesión
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        Window.clearcolor = (248/255, 248/255, 248/255, 1)

        # Título de la aplicación
        title = Label(text='Qhali Wawa', pos_hint={'center_x': 0.5, 'top': 0.9}, size_hint=(None, None), size=(Window.width, 50), color=(0, 0, 0, 1))
        layout.add_widget(title)

        # Mensaje de error
        self.error_label = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'y': 0}, color=(1, 0, 0, 1))
        layout.add_widget(self.error_label)

        # Logo
        logo = Image(source='logo.png', size_hint=(None, None), size=(200, 200), pos_hint={'center_x': 0.5, 'center_y': 0.7})
        layout.add_widget(logo)

        # Campo de correo electrónico
        self.email = TextInput(hint_text='Correo Electrónico', size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        layout.add_widget(self.email)

        # Campo de contraseña
        self.password = TextInput(hint_text='Contraseña', password=True, size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.4})
        layout.add_widget(self.password)

        # Botón de ojo para mostrar/ocultar contraseña
        self.show_password_button = ToggleButton(text='Mostrar', size_hint=(0.1, 0.05), pos_hint={'center_x': 0.94, 'center_y': 0.4})
        self.show_password_button.bind(on_press=self.toggle_password_visibility)
        layout.add_widget(self.show_password_button)

        # Botón de inicio de sesión
        login_button = Button(text='Ingresar', size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.3}, background_normal='', background_color=(93/255, 161/255, 163/255, 1))
        login_button.bind(on_press=self.validate_credentials)
        layout.add_widget(login_button)

        # Botón de registro
        register_button = Button(text='Registrarse', size_hint=(0.76, None), height=44, background_normal='', pos_hint={'center_x': 0.5, 'center_y': 0.2}, background_color=(93/255, 161/255, 163/255, 1))
        register_button.bind(on_press=self.go_to_register)
        layout.add_widget(register_button)

        # Botón de cambiar contraseña
        register_button = Button(text='Cambiar contraseña', size_hint=(0.76, None), height=44, background_normal='', pos_hint={'center_x': 0.5, 'center_y': 0.1}, background_color=(93/255, 161/255, 163/255, 1))
        register_button.bind(on_press=self.go_to_change_password)
        layout.add_widget(register_button)

        self.add_widget(layout)

    def validate_credentials(self, instance):
        email = self.email.text
        password = self.password.text
        self.manager.database = self.manager.sheet.get_all_values()
        self.manager.database.pop(0)
        if [email, password] in list(map(lambda usuario: usuario[1:3], self.manager.database)):
            self.email.text = ''
            self.password.text = ''
            self.error_label.text = ''
            self.password.password = True
            self.show_password_button.text = 'Mostrar'
            self.show_password_button.state = 'normal'
            index = list(map(lambda usuario: usuario[1:3], self.manager.database)).index([email, password])
            data = self.manager.database[index]
            data[4:6] = list(map(int, data[4:6]))
            self.manager.sheet.delete_rows(index+2)
            self.manager.sheet.append_row(data)
            self.manager.database = self.manager.sheet.get_all_values()
            self.manager.database.pop(0)
            self.manager.transition.direction = 'left'
            self.manager.current = 'patient_info_screen'
        else:
            self.error_label.text = 'Credenciales incorrectas.'

    def go_to_register(self, button):
        self.email.text = ''
        self.password.text = ''
        self.error_label.text = ''
        self.password.password = True
        self.show_password_button.text = 'Mostrar'
        self.show_password_button.state = 'normal'
        self.manager.transition.direction = 'left'
        self.manager.current = 'register_screen'

    def go_to_change_password(self, instance):
        self.email.text = ''
        self.password.text = ''
        self.error_label.text = ''
        self.password.password = True
        self.show_password_button.text = 'Mostrar'
        self.show_password_button.state = 'normal'
        self.manager.transition.direction = 'left'
        self.manager.current = 'change_password_screen_1'

    def toggle_password_visibility(self, instance):
        if self.password.password:
            self.password.password = False
            self.show_password_button.text = 'Ocultar'
        else:
            self.password.password = True
            self.show_password_button.text = 'Mostrar'

# Pantalla de información del paciente
class PatientInfoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=70, spacing=70)

        # Botón con imagen de usuario
        self.user_button = ImageButton(source='user_icon.png', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.1, 'center_y': 1})
        self.user_button.bind(on_press=self.open_dropdown)
        layout.add_widget(self.user_button)

        # Crear el dropdown
        self.dropdown = DropDown()

        # Botón para cambiar contraseña
        change_password_button = Button(text='Cambiar contraseña', size_hint=(0.3, None), height=44, pos_hint={'center_x': 0.1, 'center_y': 0.8})
        change_password_button.bind(on_release=self.go_to_change_password)
        self.dropdown.add_widget(change_password_button)

        # Botón para cerrar sesión
        logout_button = Button(text='Cerrar sesión', size_hint=(0.3, None), height=44, pos_hint={'center_x': 0.1, 'center_y': 0.7})
        logout_button.bind(on_release=self.logout)
        self.dropdown.add_widget(logout_button)

        # Título de bienvenida
        title_label = Label(text='¡Bienvenido! Elija un ecógrafo:', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5}, color=(0, 0, 0, 1))
        layout.add_widget(title_label)

        # Botón para ecógrafo Siemens
        siemens_button = ImageButton(source="12687-2-siemens-acuson-p500-cart.jpg", size_hint=(None, None), width=150, height=150, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        siemens_button.bind(on_press=lambda x: self.change_screen('siemens_screen_1'))
        layout.add_widget(siemens_button)

        # Botón para ecógrafo Dräger
        drager_button = ImageButton(source="philips-clearvue-550.jpg", size_hint=(None, None), width=150, height=150, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        drager_button.bind(on_press=lambda x: self.change_screen('drager_screen_1'))
        layout.add_widget(drager_button)

        self.add_widget(layout)

    def open_dropdown(self, instance):
        self.dropdown.open(self.user_button)

    def logout(self, instance):
        self.dropdown.dismiss()
        self.manager.transition.direction = 'right'
        self.manager.current = 'login_screen'

    def go_to_change_password(self, instance):
        self.dropdown.dismiss()
        self.manager.type = 'password'
        self.manager.transition.direction = 'right'
        self.manager.current = 'two_step_verification_screen'
        
    def change_screen(self, screen_name):
        self.manager.transition.direction = 'left'
        self.manager.current = screen_name
        
# Pantalla para el ecógrafo Siemens
class SiemensScreen1(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Flecha de regreso
        back_arrow = ImageButton(source='flecha.png', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.1, 'center_y': 0.9})
        back_arrow.bind(on_press=self.go_to_patient_info)
        layout.add_widget(back_arrow)

        # Título
        title = Label(text='Tutorial\nEncendido del Ecógrafo e Inicio de Sesión', size_hint=(1, None), height=50, color=(0, 0, 0, 1), font_size='20sp', halign='center')
        title.bind(size=title.setter('text_size'))  # Permite que el tamaño del texto se ajuste al tamaño del widget

        # Imagen de botón de encendido
        on_off_button = Image(source='Botón de encendido.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5, 'center_y': 0.76})
        layout.add_widget(on_off_button)

        # Descripción con ajuste de texto
        description = Label(text='Presione el botón de encendido. \nPara iniciar sesión, escriba "admin" en user y haga click izquierdo en el botón "ok".', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), color=(0, 0, 0, 1), font_size='16sp')
        description.bind(size=description.setter('text_size'))  # Actualiza el tamaño del texto cuando el tamaño del Label cambia

        # Botón para la siguiente instrucción
        next_instruction_button = Button(text="Siguiente Instrucción", size_hint=(None, None), width=200, height=40, pos_hint={'center_x': 0.5, 'center_y': 0.1})
        next_instruction_button.bind(on_press=self.next_instruction)

        # Añadir widgets al layout
        layout.add_widget(title)
        layout.add_widget(description)
        layout.add_widget(next_instruction_button)

        self.add_widget(layout)
        
    def next_instruction(self, instance):
        self.manager.transition.direction = 'left'
        self.manager.current = 'siemens_screen_2'

    def go_to_patient_info(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'patient_info_screen'
        
# Pantalla de instrucción siguiente con botón para ir a más instrucciones
class SiemensScreen2(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Título
        title = Label(text='Tutorial\nRegistro del paciente', size_hint=(1, None), height=50, color=(0, 0, 0, 1), font_size='20sp', halign='center')
        title.bind(size=title.setter('text_size'))  # Permite que el tamaño del texto se ajuste al tamaño del widget

        # Imagen de botón de encendido
        patient_button = Image(source='Botón de patient.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5, 'center_y': 0.76})
        layout.add_widget(patient_button)

        # Descripción con ajuste de texto
        description = Label(text='Presione el botón "Patient" y registre los datos del paciente, luego haga click izquierdo en el botón "ok".', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), color=(0, 0, 0, 1), font_size='16sp')
        description.bind(size=description.setter('text_size'))  # Actualiza el tamaño del texto cuando el tamaño del Label cambia
        
        # Botón para la instrucción anterior
        previous_instruction_button = Button(text="Instrucción Anterior", size_hint=(None, None), width=200, height=40)
        previous_instruction_button.bind(on_press=self.previous_instruction)
        
        # Botón para la siguiente instrucción
        next_instruction_button = Button(text="Siguiente Instrucción", size_hint=(None, None), width=200, height=40)
        next_instruction_button.bind(on_press=self.next_instruction)

        # Añadir un contenedor para los botones
        button_container = BoxLayout(size_hint=(1, None), height=40)
        button_container.add_widget(previous_instruction_button)
        button_container.add_widget(Widget())  # Espaciador
        button_container.add_widget(next_instruction_button)

        # Añadir widgets al layout
        layout.add_widget(title)
        layout.add_widget(description)
        layout.add_widget(button_container)

        self.add_widget(layout)

    def previous_instruction(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'siemens_screen_1'
    
    def next_instruction(self, instance):
        self.manager.transition.direction = 'left'
        self.manager.current = 'siemens_screen_3'

class SiemensScreen3(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Título
        title = Label(text='Tutorial\nSelección de preajuste', size_hint=(1, None), height=50, color=(0, 0, 0, 1), font_size='20sp', halign='center')
        title.bind(size=title.setter('text_size'))  # Permite que el tamaño del texto se ajuste al tamaño del widget

        # Imagen de botón de encendido
        patient_button = Image(source='Botón de exam.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5, 'center_y': 0.76})
        layout.add_widget(patient_button)

        # Descripción con ajuste de texto
        description = Label(text='Presione el botón "Exam" y elija el preajuste adecuado.', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), color=(0, 0, 0, 1), font_size='16sp')
        description.bind(size=description.setter('text_size'))  # Actualiza el tamaño del texto cuando el tamaño del Label cambia
        
        # Botón para la instrucción anterior
        previous_instruction_button = Button(text="Instrucción Anterior", size_hint=(None, None), width=200, height=40)
        previous_instruction_button.bind(on_press=self.previous_instruction)
        
        # Botón para la siguiente instrucción
        next_instruction_button = Button(text="Siguiente Instrucción", size_hint=(None, None), width=200, height=40)
        next_instruction_button.bind(on_press=self.next_instruction)

        # Añadir un contenedor para los botones
        button_container = BoxLayout(size_hint=(1, None), height=40)
        button_container.add_widget(previous_instruction_button)
        button_container.add_widget(Widget())  # Espaciador
        button_container.add_widget(next_instruction_button)

        # Añadir widgets al layout
        layout.add_widget(title)
        layout.add_widget(description)
        layout.add_widget(button_container)

        self.add_widget(layout)

    def previous_instruction(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'siemens_screen_2'
    
    def next_instruction(self, instance):
        self.manager.transition.direction = 'left'
        self.manager.current = 'siemens_screen_4'

class SiemensScreen4(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Título
        title = Label(text='Tutorial\nAutoajuste', size_hint=(1, None), height=50, color=(0, 0, 0, 1), font_size='20sp', halign='center')
        title.bind(size=title.setter('text_size'))  # Permite que el tamaño del texto se ajuste al tamaño del widget

        # Imagen de botón de encendido
        patient_button = Image(source='Botón de autoset.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5, 'center_y': 0.76})
        layout.add_widget(patient_button)

        # Descripción con ajuste de texto
        description = Label(text='Presione este botón para ajustar automáticamente la imagen ecográfica.\n¡Ahora está listo(a) para realizar la ecografía!', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), color=(0, 0, 0, 1), font_size='16sp')
        description.bind(size=description.setter('text_size'))  # Actualiza el tamaño del texto cuando el tamaño del Label cambia
        
        # Botón para la instrucción anterior
        previous_instruction_button = Button(text="Instrucción Anterior", size_hint=(None, None), width=200, height=40, pos_hint={'center_x': 0.5, 'center_y': 0.2})
        previous_instruction_button.bind(on_press=self.previous_instruction)
        
        # Botón para la siguiente instrucción
        start_measurement_button = Button(text="Iniciar Medición", size_hint=(None, None), width=200, height=40, pos_hint={'center_x': 0.5, 'center_y': 0.1})
        start_measurement_button.bind(on_press=self.show_instructions)

        # Añadir widgets al layout
        layout.add_widget(title)
        layout.add_widget(description)
        layout.add_widget(previous_instruction_button)
        layout.add_widget(start_measurement_button)

        self.add_widget(layout)

    def previous_instruction(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'siemens_screen_3'
    
    def show_instructions(self, instance):
        box_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_label = Label(text="Coloque el celular en el visor y ajústelo.")
        accept_button = Button(text="Continuar", size_hint=(1, 0.4))

        box_layout.add_widget(popup_label)
        box_layout.add_widget(accept_button)

        self.popup = Popup(title="Instrucción de la Colocación del celular", content=box_layout, size_hint=(None, None), size=(400, 200), auto_dismiss=False)
        accept_button.bind(on_press=self.proceed_to_measurement)

        self.popup.open()

    def proceed_to_measurement(self, instance):
        """Cerrar el popup y cambiar a la pantalla de medición."""
        self.popup.dismiss()
        # Asegurarse de cambiar a la pantalla correcta
        self.manager.transition.direction = 'left'
        self.manager.current = 'new_measurement_screen'

## Pantalla para el ecógrafo Dräger
class DragerScreen1(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10, height=30)

        # Botón para iniciar medición
        start_measurement_button = Button(text="Iniciar Medición", size_hint=(None, None), width=200, height=40)
        start_measurement_button.bind(on_press=lambda x: self.change_screen())
        layout.add_widget(start_measurement_button)

        self.add_widget(layout)

    def change_screen(self, screen_name):
        self.manager.transition.direction = 'left'
        self.manager.current = screen_name

class NewMeasurementScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        # Flecha de regreso
        back_arrow = ImageButton(source='flecha.png', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.1, 'center_y': 0.9})
        back_arrow.bind(on_press=self.go_to_patient_info)
        self.layout.add_widget(back_arrow)
        
        self.camera_widget = Image(size_hint=(1, 0.9))
        self.layout.add_widget(self.camera_widget)

        self.camera_button = Button(text="Prender Cámara", size_hint=(1, 0.1))
        self.camera_button.bind(on_press=self.toggle_camera)
        self.layout.add_widget(self.camera_button)

        self.add_widget(self.layout)
        
        self.capture = None

        # URL de la transmisión de la cámara IP del celular
        self.camera_ip_url = 'http://10.100.99.122:8080/video'
        
        # Rangos HSV para el color verde fosforescente
        self.verdeBajo = np.array([35, 100, 100], np.uint8)
        self.verdeAlto = np.array([85, 255, 255], np.uint8)

        # Estado para controlar el modo de visualización
        self.modo_visualizacion = 0  # 0 = Primer paso, 1 = Segundo paso, 2 = Tercer paso, 3 = Cuarto paso

        # Función para manejar los clics del mouse
        def on_click(x, y, button, pressed):
            if pressed:
                self.modo_visualizacion = (self.modo_visualizacion + 1) % 14  # Ciclar entre 0 y 3

        # Iniciar el oyente del mouse en un hilo aparte
        listener = MouseListener(on_click=on_click)
        listener.start()

    def go_to_patient_info(self, instance):
        if self.capture is not None:
            if self.capture.isOpened():
                self.capture.release()
                self.capture = None
                self.camera_button.text = "Prender Cámara"
                self.camera_widget.texture = None
        self.manager.transition.direction = 'right'
        self.manager.current = 'patient_info_screen'
    
    def toggle_camera(self, *args):
        if self.capture is None:
            self.capture = cv2.VideoCapture(self.camera_ip_url)
            if self.capture.isOpened():
                self.camera_button.text = "Apagar Cámara"
                Clock.schedule_interval(self.update, 1.0 / 30.0)  # Actualizar a 30 FPS
            else:
                self.capture.release()
                self.capture = None
                self.camera_button.text = "Prender Cámara"
                self.camera_widget.texture = None
        else:
            Clock.unschedule(self.update)
            self.capture.release()
            self.capture = None
            self.camera_button.text = "Prender Cámara"
            self.camera_widget.texture = None
        
    def update(self, dt):
        if self.capture is not None and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                frameHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                maskVerde = cv2.inRange(frameHSV, self.verdeBajo, self.verdeAlto)
                contornos, _ = cv2.findContours(maskVerde, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                overlay = frame.copy()
                for contorno in contornos:
                    area = cv2.contourArea(contorno)
                    if area > 500:
                        M = cv2.moments(contorno)
                        if M["m00"] != 0:
                            cX = int(M["m10"] / M["m00"])
                            cY = int(M["m01"] / M["m00"])

                        if self.modo_visualizacion == 0:
                            cv2.drawContours(overlay, [contorno], 0, (0, 0, 255), thickness=cv2.FILLED)
                            cv2.circle(overlay, (cX, cY), 5, (0, 0, 255), -1)
                            cv2.putText(overlay, f"APLICAR GEL EN EL AREA: (X: {cX}, Y: {cY}, Area: {int(area)})", (cX - 50, cY - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

                        elif self.modo_visualizacion == 1:
                            epsilon = 0.01 * cv2.arcLength(contorno, True)
                            approx = cv2.approxPolyDP(contorno, epsilon, True)
                            points = approx.squeeze()
                            selected_points = points[np.round(np.linspace(0, len(points) - 1, 6)).astype(int)]
                            for (x, y) in selected_points:
                                cv2.circle(overlay, (x, y), 20, (0, 0, 255), -1)
                            cv2.putText(overlay, "DISTRIBUIR UNIFORMEMENTE EL GEL EN LA ZONA DESEADA", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

                        elif self.modo_visualizacion == 2:
                            cv2.putText(overlay, "COLOQUE EL NOTCH EN LA PARTE DERECHA DEL PACIENTE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

                        elif self.modo_visualizacion == 3:
                            cv2.drawContours(overlay, [contorno], 0, (0, 0, 255), thickness=cv2.FILLED)
                            topmost = tuple(contorno[contorno[:, :, 1].argmin()][0])
                            bbox = cv2.boundingRect(contorno)
                            center_x = bbox[0] + bbox[2] // 2
                            center_y = topmost[1] + 50  # Incrementado el desplazamiento vertical para asegurar que el arco está debajo de la línea superior

                            # Dibuja el arco centrado horizontalmente en la parte superior ajustada
                            cv2.ellipse(overlay, (center_x, center_y), (30, 10), 270, 0, 180, (0, 0, 0), 4)
                            cv2.putText(overlay, f"ARCO (X: {center_x}, Y: {center_y}, Area: {int(area)})", (center_x - 50, center_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                        elif self.modo_visualizacion == 4:
                            for contorno in contornos:
                                area = cv2.contourArea(contorno)
                                if area > 500:  # Asegurándonos de que el contorno es lo suficientemente grande
                                    bbox = cv2.boundingRect(contorno)
                                    x, y, w, h = bbox

                                    area_frame = 10000  # Supongamos que este es el área del marco dentro del cual debe estar el contorno
                                    if area > 0.8 * area_frame:  # Condición adicional para que el contorno sea grande suficiente

                                        M = cv2.moments(contorno)
                                        if M["m00"] != 0:
                                            cX = int(M["m10"] / M["m00"])  # Centroide x del contorno
                                            cY = int(M["m01"] / M["m00"])  # Centroide y del contorno

                                            cm_to_pixels = 20  # Suponiendo que 1 cm equivale a 20 píxeles
                                            # Calcula la posición de las líneas blancas en base al centroide del contorno
                                            left_line_x = cX - (2 * cm_to_pixels)
                                            right_line_x = cX + (2 * cm_to_pixels)
                                            # Dibuja las líneas blancas dentro del marco del contorno
                                            cv2.line(overlay, (left_line_x, y), (left_line_x, y + h), (255, 255, 255), 2)
                                            cv2.line(overlay, (right_line_x, y), (right_line_x, y + h), (255, 255, 255), 2)

                                        # Posiciona y muestra el texto "DESLIZA!"
                                        text_position = (x + w // 2 - 60, y + h + 20)  # Ajusta la posición del texto debajo del contorno
                                        cv2.putText(overlay, "DESLIZA", text_position, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                        elif self.modo_visualizacion == 5:
                            cv2.drawContours(overlay, [contorno], 0, (0, 0, 255), thickness=cv2.FILLED)
                            bbox = cv2.boundingRect(contorno)
                            center_x = bbox[0] + bbox[2] // 2  # Centro horizontal del contorno
                            center_y = bbox[1] + bbox[3] - 20  # Posiciona el centro del arco un poco por encima del borde inferior del contorno
                            radius_x = min(30, bbox[2] // 4)  # Ajusta el radio horizontal para que no exceda el ancho del contorno
                            radius_y = min(10, bbox[3] // 10)  # Ajusta el radio vertical para que no exceda la altura del contorno
                            cv2.ellipse(overlay, (center_x, center_y), (radius_x, radius_y), 270, 0, 180, (0, 0, 0), 4)
                            cv2.putText(overlay, "ARCO", (center_x - 50, center_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                        
                        elif self.modo_visualizacion == 6:
                            cv2.putText(overlay, "COLOQUE EL TRANSDUCTOR DEBAJO DE LAS COSTILLAS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                        
                        elif self.modo_visualizacion == 7:
                            for contorno in contornos:
                                area = cv2.contourArea(contorno)
                                if area > 500:  # Asegurándonos de que el contorno es lo suficientemente grande
                                    bbox = cv2.boundingRect(contorno)
                                    x, y, w, h = bbox

                                    M = cv2.moments(contorno)
                                    if M["m00"] != 0:
                                        cX = int(M["m10"] / M["m00"])  # Centroide x del contorno
                                        cm_to_pixels = 20  # Suponiendo que 1 cm equivale a 20 píxeles

                                        # Calcula la posición de la línea izquierda en base al centroide del contorno
                                        left_line_x = cX - (2 * cm_to_pixels)

                                        # Posición del nuevo arco en la mitad de la línea izquierda
                                        arc_center_x = left_line_x
                                        arc_center_y = y + h // 2

                                        cv2.ellipse(overlay, (arc_center_x, arc_center_y), (30, 10), 270, 0, 180, (0, 0, 0), 4)
                                        cv2.putText(overlay, "ARCO", (arc_center_x - 50, arc_center_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                        elif self.modo_visualizacion == 8:
                            for contorno in contornos:
                                area = cv2.contourArea(contorno)
                                if area > 500:  # Asegurándonos de que el contorno es lo suficientemente grande
                                    bbox = cv2.boundingRect(contorno)
                                    x, y, w, h = bbox

                                    M = cv2.moments(contorno)
                                    if M["m00"] != 0:
                                        cX = int(M["m10"] / M["m00"])  # Centroide x del contorno
                                        cm_to_pixels = 20  # Suponiendo que 1 cm equivale a 20 píxeles

                                        # Antigua línea izquierda ahora como línea derecha
                                        new_right_line_x = cX - (2 * cm_to_pixels)
                                        # Nueva línea izquierda, 2 cm a la izquierda de la nueva línea derecha
                                        new_left_line_x = new_right_line_x - (2 * cm_to_pixels)

                                        # Dibuja las líneas blancas dentro del marco del contorno
                                        cv2.line(overlay, (new_right_line_x, y), (new_right_line_x, y + h), (255, 255, 255), 2)
                                        cv2.line(overlay, (new_left_line_x, y), (new_left_line_x, y + h), (255, 255, 255), 2)

                                    # Posiciona y muestra el texto "DESLIZA!"
                                    text_position = (x + w // 2 - 60, y + h + 20)  # Ajusta la posición del texto debajo del contorno
                                    cv2.putText(overlay, "DESLIZA", text_position, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                        elif self.modo_visualizacion == 9:
                            for contorno in contornos:
                                area = cv2.contourArea(contorno)
                                if area > 500:  # Asegurándonos de que el contorno es lo suficientemente grande
                                    bbox = cv2.boundingRect(contorno)
                                    x, y, w, h = bbox

                                    M = cv2.moments(contorno)
                                    if M["m00"] != 0:
                                        cX = int(M["m10"] / M["m00"])  # Centroide x del contorno
                                        cm_to_pixels = 20  # Suponiendo que 1 cm equivale a 20 píxeles

                                        # Calcula la posición de la línea izquierda en base al centroide del contorno
                                        left_line_x = cX - (2 * cm_to_pixels)

                                        # Posición del nuevo arco en la parte inferior de la línea izquierda
                                        arc_center_x = left_line_x
                                        arc_center_y = y + h - 10  # Ajuste para posicionar el arco dentro del contorno cerca del borde inferior

                                        # Dibuja el arco con los mismos parámetros de tamaño y orientación
                                        cv2.ellipse(overlay, (arc_center_x, arc_center_y), (30, 10), 270, 0, 180, (0, 0, 0), 4)
                                        cv2.putText(overlay, "ARCO", (arc_center_x - 50, arc_center_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                        elif self.modo_visualizacion == 10:
                            cv2.putText(overlay, "COLOQUE EL TRANSDUCTOR DEBAJO DE LAS COSTILLAS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                        
                        elif self.modo_visualizacion == 11:
                            for contorno in contornos:
                                area = cv2.contourArea(contorno)
                                if area > 500:  # Asegurándonos de que el contorno es lo suficientemente grande
                                    bbox = cv2.boundingRect(contorno)
                                    x, y, w, h = bbox

                                    M = cv2.moments(contorno)
                                    if M["m00"] != 0:
                                        cX = int(M["m10"] / M["m00"])  # Centroide x del contorno
                                        cm_to_pixels = 20  # Suponiendo que 1 cm equivale a 20 píxeles

                                        # Calcula la posición de la línea derecha en base al centroide del contorno
                                        right_line_x = cX - (3 * cm_to_pixels)  # Alineado con la definición del modo 11

                                        # Posición del nuevo arco en el centro vertical de la línea derecha
                                        arc_center_x = right_line_x
                                        arc_center_y = y + h // 2  # Ajuste para posicionar el arco en el centro vertical de la línea

                                        # Dibuja el arco con los mismos parámetros de tamaño y orientación
                                        cv2.ellipse(overlay, (arc_center_x, arc_center_y), (30, 10), 270, 0, 180, (0, 0, 0), 4)
                                        cv2.putText(overlay, "ARCO", (arc_center_x - 50, arc_center_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                        elif self.modo_visualizacion == 12:
                            for contorno in contornos:
                                area = cv2.contourArea(contorno)
                                if area > 500:  # Asegurándonos de que el contorno es lo suficientemente grande
                                    bbox = cv2.boundingRect(contorno)
                                    x, y, w, h = bbox

                                    M = cv2.moments(contorno)
                                    if M["m00"] != 0:
                                        cX = int(M["m10"] / M["m00"])  # Centroide x del contorno
                                        cm_to_pixels = 20  # Suponiendo que 1 cm equivale a 20 píxeles

                                        # Antigua línea izquierda ahora como línea derecha
                                        new_right_line_x = cX - (3 * cm_to_pixels)
                                        # Nueva línea izquierda, 2 cm a la izquierda de la nueva línea derecha
                                        new_left_line_x = new_right_line_x - (3 * cm_to_pixels)

                                        # Dibuja las líneas blancas dentro del marco del contorno
                                        cv2.line(overlay, (new_right_line_x, y), (new_right_line_x, y + h), (255, 255, 255), 2)
                                        cv2.line(overlay, (new_left_line_x, y), (new_left_line_x, y + h), (255, 255, 255), 2)

                                    # Posiciona y muestra el texto "DESLIZA!"
                                    text_position = (x + w // 2 - 60, y + h + 20)  # Ajusta la posición del texto debajo del contorno
                                    cv2.putText(overlay, "DESLIZA", text_position, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                        elif self.modo_visualizacion == 13:
                            for contorno in contornos:
                                area = cv2.contourArea(contorno)
                                if area > 500:  # Asegurándonos de que el contorno es lo suficientemente grande
                                    bbox = cv2.boundingRect(contorno)
                                    x, y, w, h = bbox

                                    M = cv2.moments(contorno)
                                    if M["m00"] != 0:
                                        cX = int(M["m10"] / M["m00"])  # Centroide x del contorno
                                        cm_to_pixels = 20  # Suponiendo que 1 cm equivale a 20 píxeles

                                        # Calcula la posición de la línea derecha en base al centroide del contorno
                                        right_line_x = cX - (3 * cm_to_pixels)  # Alineado con la definición del modo 11

                                        # Posición del nuevo arco en la parte inferior de la línea derecha
                                        arc_center_x = right_line_x
                                        arc_center_y = y + h - 10  # Ajuste para posicionar el arco cerca del borde inferior de la línea

            alpha = 0.4
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

            # Convertir el frame a textura para Kivy
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tobytes()
            image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.camera_widget.texture = image_texture

# Pantalla de registro
class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout(size=Window.size)
        Window.clearcolor = (248/255, 248/255, 248/255, 1)  # Fondo #F8F8F8

        # Flecha de regreso
        back_arrow = ImageButton(source='flecha.png', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.1, 'center_y': 0.9})
        back_arrow.bind(on_press=self.go_to_login)
        layout.add_widget(back_arrow)

        # Título registro
        register_label = Label(text='Registro', size_hint=(None, None), size=(Window.width, 50), pos_hint={'center_x': 0.5, 'center_y': 0.9}, color=(0, 0, 0, 1))
        layout.add_widget(register_label)
        
        # Logo
        logo = Image(source='logo.png', size_hint=(None, None), size=(130, 130), pos_hint={'center_x': 0.5, 'center_y': 0.76})
        layout.add_widget(logo)

        # Títulos de los campos de registro
        
        # Nombres y apellidos
        self.name_input = TextInput(hint_text='Nombre Completo', size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.6})
        layout.add_widget(self.name_input)

        # Error nombres y apellidos
        self.error_name = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'y': 0.52}, color=(1, 0, 0, 1))  # Color del mensaje de error rojo
        layout.add_widget(self.error_name)

        # Correo electrónico
        self.email = TextInput(hint_text='Correo Electrónico', size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        layout.add_widget(self.email)

        # Error correo electrónico
        self.error_email = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'y': 0.42}, color=(1, 0, 0, 1))  # Color del mensaje de error rojo
        layout.add_widget(self.error_email)
        
        # Contraseña
        self.password = TextInput(hint_text='Contraseña', password=True, size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.4})
        layout.add_widget(self.password)

        # Botón de ojo para mostrar/ocultar contraseña
        self.show_password_button = ToggleButton(text='Mostrar', size_hint=(0.1, 0.05), pos_hint={'center_x': 0.95, 'center_y': 0.4})
        self.show_password_button.bind(on_press=self.toggle_password_visibility)
        layout.add_widget(self.show_password_button)
        
        # Error contraseña
        self.error_password = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'center_y': 0.35}, color=(1, 0, 0, 1))  # Color del mensaje de error rojo
        layout.add_widget(self.error_password)

        # Repetir contraseña
        self.confirm_password = TextInput(hint_text='Repetir Contraseña', password=True, size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.3})
        layout.add_widget(self.confirm_password)

        # Botón de registrarse
        register_button = Button(text="Registrarse", size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.2}, background_normal='', background_color = (93/255, 161/255, 163/255, 1))  # Botón con fondo #8FC5AB
        register_button.bind(on_press=self.save_to_database)
        layout.add_widget(register_button)

        # Error repetir contraseña
        self.error_confirm_password = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'y': 0.1}, color=(1, 0, 0, 1))  # Color del mensaje de error rojo
        layout.add_widget(self.error_confirm_password)

        self.add_widget(layout)
        self.error = [0]*5
        self.popup = None
        
    def go_to_login(self, instance):
        self.name_input.text = ''
        self.email.text = ''
        self.password.text = ''
        self.confirm_password.text = ''
        self.error_name.text = ''
        self.error_email.text = ''
        self.error_password.text = ''
        self.error_confirm_password.text = ''
        self.password.password = True
        self.show_password_button.text = 'Mostrar'
        self.show_password_button.state = 'normal'
        if self.popup:
            self.popup.dismiss()
        self.manager.transition.direction = 'right'
        self.manager.current = 'login_screen'
        
    def save_to_database(self, instance):
        self.manager.database = self.manager.sheet.get_all_values()
        self.manager.database.pop(0)
        name = self.name_input.text
        email = self.email.text
        password = self.password.text
        confirm_password = self.confirm_password.text
        if email in list(map(lambda Usuario: Usuario[1], self.manager.database)):
            self.error[0] = 1
            self.show_email_already_registered_popup()
            return
        else:
            self.error[0] = 0
        if not ''.join(name.split()).isalpha():
            self.error[1] = 1
            self.error_name.text = 'El nombre solo puede contener letras y espacios.'
        else:
            self.error[1] = 0
            self.error_name.text = ''
        if (not email.replace('.', '').replace('@', '', 1).isalnum()) or ('@' not in email) or ('.' not in email):
            self.error[2] = 1
            self.error_email.text = 'Correo electrónico inválido.'
        else:
            self.error[2] = 0
            self.error_email.text = ''
        if (len(password)<10) or (not any(list(map(lambda Carácter: Carácter.isupper(), list(password))))) or (not any(list(map(lambda Carácter: Carácter.islower(), list(password))))) or (not any(list(map(lambda Carácter: Carácter.isnumeric(), list(password))))):
            self.error[3] = 1
            self.error_password.text = 'La contraseña debe tener al menos 10 caracteres y debe contener mayúsculas, minúsculas y números.'
        else:
            self.error[3] = 0
            self.error_password.text = ''
        if password != confirm_password:
            self.error[4] = 1
            self.error_confirm_password.text = 'Las contraseñas no coinciden.'
        else:
            self.error[4] = 0
            self.error_confirm_password.text = ''
        if not any(self.error):
            self.name_input.text = ''
            self.email.text = ''
            self.password.text = ''
            self.confirm_password.text = ''
            self.error_name.text = ''
            self.error_email.text = ''
            self.error_password.text = ''
            self.error_confirm_password.text = ''
            self.password.password = True
            self.show_password_button.text = 'Mostrar'
            self.show_password_button.state = 'normal'
            self.manager.type = 'register'
            self.manager.sheet.append_row([name, email, password, None, 1, 1])
            self.manager.database = self.manager.sheet.get_all_values()
            self.manager.database.pop(0)
            self.manager.transition.direction = 'left'
            self.manager.current = 'two_step_verification_screen'

    def show_email_already_registered_popup(self):
        box = FloatLayout()
        return_to_login_label = Label(text='Este correo electrónico ya ha sido registrado', size_hint=(1, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.7})
        return_to_login_button = Button(text='Inicie sesión', size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.2})
        box.add_widget(return_to_login_label)
        box.add_widget(return_to_login_button)
        self.popup = Popup(title='Correo electrónico ya registrado', content=box, size_hint=(None, None), size=(400, 200))
        return_to_login_button.bind(on_press=self.go_to_login)
        self.popup.open()

    def toggle_password_visibility(self, instance):
        if self.password.password:
            self.password.password = False
            self.show_password_button.text = 'Ocultar'
            self.confirm_password.password = False
        else:
            self.password.password = True
            self.show_password_button.text = 'Mostrar'
            self.confirm_password.password = True

class ChangePasswordScreen1(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout(size=Window.size)
        Window.clearcolor = (248/255, 248/255, 248/255, 1)  # Fondo #F8F8F8

        # Flecha de regreso
        back_arrow = ImageButton(source='flecha.png', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.1, 'center_y': 0.9})
        back_arrow.bind(on_press=self.go_to_login)
        layout.add_widget(back_arrow)

        # Título cambiar contraseña
        change_password_label = Label(text='Cambiar Contraseña', size_hint=(None, None), size=(Window.width, 50), pos_hint={'center_x': 0.5, 'center_y': 0.9}, color=(0, 0, 0, 1))
        layout.add_widget(change_password_label)
        
        # Logo
        logo = Image(source='logo.png', size_hint=(None, None), size=(130, 130), pos_hint={'center_x': 0.5, 'center_y': 0.76})
        layout.add_widget(logo)

        # Correo electrónico
        self.email = TextInput(hint_text='Correo Electrónico', size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        layout.add_widget(self.email)

        # Error correo electrónico
        self.error_email = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'y': 0.42}, color=(1, 0, 0, 1))  # Color del mensaje de error rojo
        layout.add_widget(self.error_email)

        # Botón "Siguiente"
        next_button = Button(text="Siguiente", size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.2}, background_normal='', background_color = (93/255, 161/255, 163/255, 1))  # Botón con fondo #8FC5AB
        next_button.bind(on_press=self.next)
        layout.add_widget(next_button)
        self.add_widget(layout)

    def go_to_login(self, instance):
        self.email.text = ''
        self.error_email.text = ''
        self.manager.transition.direction = 'right'
        self.manager.current = 'login_screen'

    def next(self, instance):
        self.manager.database = self.manager.sheet.get_all_values()
        self.manager.database.pop(0)
        email = self.email.text
        if email not in list(map(lambda Usuario: Usuario[1], self.manager.database)):
            self.error_email.text = 'Este correo electrónico no ha sido registrado'
        else:
            self.email.text = ''
            self.error_email.text = ''
            email_index = list(map(lambda Usuario: Usuario[1], self.manager.database)).index(email)
            data = self.manager.database[email_index]
            data[4:6] = list(map(int, data[4:6]))
            self.manager.sheet.delete_rows(email_index+2)
            self.manager.sheet.append_row(data)
            self.manager.database = self.manager.sheet.get_all_values()
            self.manager.database.pop(0)
            self.manager.type = 'password'
            self.manager.transition.direction = 'left'
            self.manager.current = 'two_step_verification_screen'
        
class ChangePasswordScreen2(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout(size=Window.size)
        Window.clearcolor = (248/255, 248/255, 248/255, 1)  # Fondo #F8F8F8

        # Flecha de regreso
        back_arrow = ImageButton(source='flecha.png', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.1, 'center_y': 0.9})
        back_arrow.bind(on_press=self.show_return_popup)
        layout.add_widget(back_arrow)

        # Título cambiar contraseña
        change_password_label = Label(text='Cambiar Contraseña', size_hint=(None, None), size=(Window.width, 50), pos_hint={'center_x': 0.5, 'center_y': 0.9}, color=(0, 0, 0, 1))
        layout.add_widget(change_password_label)
        
        # Logo
        logo = Image(source='logo.png', size_hint=(None, None), size=(130, 130), pos_hint={'center_x': 0.5, 'center_y': 0.76})
        layout.add_widget(logo)
        
        # Contraseña
        self.password = TextInput(hint_text='Contraseña', password=True, size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.4})
        layout.add_widget(self.password)
        
        # Error contraseña
        self.error_password = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'center_y': 0.35}, color=(1, 0, 0, 1))  # Color del mensaje de error rojo
        layout.add_widget(self.error_password)

        # Botón de ojo para mostrar/ocultar contraseña
        self.show_password_button = ToggleButton(text='Mostrar', size_hint=(0.1, 0.05), pos_hint={'center_x': 0.94, 'center_y': 0.4})
        self.show_password_button.bind(on_press=self.toggle_password_visibility)
        layout.add_widget(self.show_password_button)

        # Repetir contraseña
        self.confirm_password = TextInput(hint_text='Repetir Contraseña', password=True, size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.3})
        layout.add_widget(self.confirm_password)

        # Botón cambiar contraseña
        enter_button = Button(text='Cambiar Contraseña', size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.2}, background_normal='', background_color = (93/255, 161/255, 163/255, 1))  # Botón con fondo #8FC5AB
        enter_button.bind(on_press=self.change_password)
        layout.add_widget(enter_button)

        # Error repetir contraseña
        self.error_confirm_password = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'center_y': 0.15}, color=(1, 0, 0, 1))
        layout.add_widget(self.error_confirm_password)

        self.add_widget(layout)
        self.error = [0]*2
        
    def show_return_popup(self, instance):
        box = FloatLayout()
        label_1 = Label(text='¿Está seguro de que desea regresar?', size_hint=(1, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.75})
        label_2 = Label(text='Todo su progreso se perderá.', size_hint=(1, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.55})
        return_button = Button(text='Regresar', size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5, 'y': 0.1})
        box.add_widget(return_button)
        box.add_widget(label_1)
        box.add_widget(label_2)
        self.popup = Popup(title='Regresar', content=box, size_hint=(None, None), size=(400, 200))
        return_button.bind(on_press=self.go_to_change_password_screen_1)
        self.popup.open()
        
    def go_to_change_password_screen_1(self, instance):
        self.password.text = ''
        self.error_password.text = ''
        self.confirm_password.text = ''
        self.error_confirm_password.text = ''
        self.password.password = True
        self.show_password_button.text = 'Mostrar'
        self.show_password_button.state = 'normal'
        self.popup.dismiss()
        self.manager.transition.direction = 'right'
        self.manager.current = 'change_password_screen_1'
        
    def toggle_password_visibility(self, instance):
        if self.password.password:
            self.password.password = False
            self.show_password_button.text = 'Ocultar'
            self.confirm_password.password = False
        else:
            self.password.password = True
            self.show_password_button.text = 'Mostrar'
            self.confirm_password.password = True

    def change_password(self, instance):
        password = self.password.text
        confirm_password = self.confirm_password.text
        if (len(password)<10) or (not any(list(map(lambda Carácter: Carácter.isupper(), list(password))))) or (not any(list(map(lambda Carácter: Carácter.islower(), list(password))))) or (not any(list(map(lambda Carácter: Carácter.isnumeric(), list(password))))):
            self.error[0] = 1
            self.error_password.text = 'La contraseña debe tener al menos 10 caracteres y debe contener mayúsculas, minúsculas y números.'
        else:
            self.error[0] = 0
            self.error_password.text = ''
        if password != confirm_password:
            self.error[1] = 1
            self.error_confirm_password.text = 'Las contraseñas no coinciden.'
        else:
            self.error[1] = 0
            self.error_confirm_password.text = ''
        if not any(self.error):
            if password == self.manager.database[-1][2]:
                self.error_confirm_password.text = 'Esta contraseña ya ha sido utilizada anteriormente.'
            else:
                self.manager.sheet.update([[password]], f'C{len(self.manager.database)+1}')
                self.manager.database = self.manager.sheet.get_all_values()
                self.manager.database.pop(0)
                box = FloatLayout()
                label = Label(text='¡Su contraseña ha sido cambiada!', size_hint=(1, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.7})
                button = Button(text='Iniciar sesión', size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5, 'y': 0.1})
                box.add_widget(button)
                self.popup = Popup(title='Éxito', content=box, size_hint=(None, None), size=(400, 200))
                box.add_widget(label)
                button.bind(on_press=self.go_to_login)
                self.popup.open()

    def go_to_login(self, instance):
        self.password.text = ''
        self.error_password.text = ''
        self.confirm_password.text = ''
        self.error_confirm_password.text = ''
        self.password.password = True
        self.show_password_button.text = 'Mostrar'
        self.show_password_button.state = 'normal'
        self.popup.dismiss()
        self.manager.transition.direction = 'right'
        self.manager.current = 'login_screen'
        
class TwoStepVerificationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout(size=Window.size)
        Window.clearcolor = (248/255, 248/255, 248/255, 1)  # Fondo #F8F8F8

        # Flecha de regreso
        back_arrow = ImageButton(source='flecha.png', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.1, 'center_y': 0.9})
        back_arrow.bind(on_press=self.show_return_popup)
        layout.add_widget(back_arrow)

        # Título verificación de 2 pasos
        register_label = Label(text='Verificación en 2 Pasos', size_hint=(None, None), size=(Window.width, 50), pos_hint={'center_x': 0.5, 'center_y': 0.9}, color=(0, 0, 0, 1))
        layout.add_widget(register_label)
        
        # Logo
        logo = Image(source='logo.png', size_hint=(None, None), size=(130, 130), pos_hint={'center_x': 0.5, 'center_y': 0.76})
        layout.add_widget(logo)
        
        layout.add_widget(Label(text='Se le ha enviado un código de verificación a su correo electrónico.', pos_hint={'center_x': 0.5, 'center_y': 0.6}, size_hint=(None, None), size=(Window.width, 30),color=(0, 0, 0, 1)))

        layout.add_widget(Label(text='Dentro de 10 minutos se le enviará un nuevo código de verificación.', pos_hint={'center_x': 0.5, 'center_y': 0.5}, size_hint=(None, None), size=(Window.width, 30),color=(0, 0, 0, 1)))

        # Código de verificación
        self.verification_code_input = TextInput(hint_text='Código de verificación', size_hint=(0.8, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.4})
        layout.add_widget(self.verification_code_input)

        # Botón de validar código
        validate_code_button = Button(text='Validar código', size_hint=(0.8, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.2}, background_normal='', background_color=(93/255, 161/255, 163/255, 1))  # Botón con fondo #5DA1A3
        validate_code_button.bind(on_press=self.validate_code)
        layout.add_widget(validate_code_button)
        self.popup = None

        # Error código de verificación
        self.error = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'y': 0}, color=(1, 0, 0, 1))  # Color del mensaje de error rojo
        layout.add_widget(self.error)

        self.add_widget(layout)
        
    def on_enter(self):
        self.send_verification_code()
        # Programar el envío de un nuevo código de verificación cada 10 minutos
        self.new_code_event = Clock.schedule_interval(self.send_verification_code, 600)
        
    def send_verification_code(self, instance=None):
        self.verification_code = ''.join(map(str, np.random.choice(range(0, 10), size=7).tolist()))
        self.manager.database[-1][3:6] = [self.verification_code, 0, 0]
        self.manager.sheet.update([[self.verification_code, 0, 0]], f'D{len(self.manager.database)+1}:F{len(self.manager.database)+1}')
        
    def show_return_popup(self, instance):
        box = FloatLayout()
        label_1 = Label(text='¿Está seguro de que desea regresar?', size_hint=(1, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.75})
        label_2 = Label(text='Todo su progreso se perderá.', size_hint=(1, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.55})
        return_button = Button(text='Regresar', size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5, 'y': 0.1})
        box.add_widget(return_button)
        box.add_widget(label_1)
        box.add_widget(label_2)
        self.popup = Popup(title='Regresar', content=box, size_hint=(None, None), size=(400, 200))
        return_button.bind(on_press=self.return_to_previous_screen)
        self.popup.open()
        
    def return_to_previous_screen(self, instance):
        Clock.unschedule(self.new_code_event)
        self.verification_code_input.text = ''
        self.error.text = ''
        self.popup.dismiss()
        self.manager.transition.direction = 'right'
        if self.manager.type == 'register':
            self.manager.sheet.delete_rows(len(self.manager.database)+1)
            self.manager.database = self.manager.sheet.get_all_values()
            self.manager.database.pop(0)
            self.manager.current = 'register_screen'
        elif self.manager.type == 'password':
            self.manager.current = 'change_password_screen_1'
        
    def validate_code(self, instance):
        if self.verification_code_input.text == self.verification_code:
            Clock.unschedule(self.new_code_event)
            self.manager.sheet.update([[1]], f'E{len(self.manager.database)+1}')
            if self.manager.type == 'register':
                self.manager.database = self.manager.sheet.get_all_values()
                self.manager.database.pop(0)
                box = FloatLayout()
                label = Label(text='', size_hint=(1, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.7})
                button = Button(text='Acceder', size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5, 'y': 0.1})
                box.add_widget(button)
                button.bind(on_press=self.go_to_patient_info)
                self.popup = Popup(title='Éxito', content=box, size_hint=(None, None), size=(400, 200))
                box.add_widget(label)
                label.text = '¡Sus datos fueron agregados a la base de datos!'
                self.popup.open()
            elif self.manager.type == 'password':
                self.manager.current = 'change_password_screen_2'
        else:
            self.error.text = 'Código de verificación incorrecto'

    def go_to_patient_info(self, instance):
        self.verification_code_input.text = ''
        self.error.text = ''
        self.popup.dismiss()
        self.manager.transition.direction = 'left'
        self.manager.current = 'patient_info_screen'

class MyScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        super(MyScreenManager, self).__init__(**kwargs)
        key = 'qhali-wawa-f65e6447e30d.json'
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = service_account.Credentials.from_service_account_file(key, scopes=scopes)
        client = gspread.authorize(creds)
        sheet_id = '1bQpZwprJFqUcZ-w3p_-1mknbUhfglNfDxdvz2vz9AaM'
        workbook = client.open_by_key(sheet_id)
        self.sheet = workbook.worksheet('Registro')
        self.database = self.sheet.get_all_values()
        self.database.pop(0)
        self.type = None
        Window.bind(on_keyboard=self.on_back_button)
        
    def on_back_button(self, window, key, *args):
        if key == 27:  # 27 is the key code for the back button on Android
            current_screen = self.current
            if current_screen == 'register_screen':
                self.get_screen('register_screen').go_to_login(None)
                return True # Return True to prevent the default behavior
            elif current_screen == 'change_password_screen_1':
                self.get_screen('change_password_screen_1').go_to_login(None)
                return True
            elif current_screen == 'two_step_verification_screen':
                self.get_screen('two_step_verification_screen').show_return_popup(None)
                return True
            elif current_screen == 'change_password_screen_2':
                self.get_screen('change_password_screen_2').show_return_popup(None)
                return True
        return False

# App principal que gestiona las pantallas
class MyApp(App):
    def build(self):
        sm = MyScreenManager()
        sm.add_widget(LoginScreen(name='login_screen'))
        sm.add_widget(RegisterScreen(name='register_screen'))
        sm.add_widget(ChangePasswordScreen1(name='change_password_screen_1'))
        sm.add_widget(ChangePasswordScreen2(name='change_password_screen_2'))
        sm.add_widget(TwoStepVerificationScreen(name='two_step_verification_screen'))
        sm.add_widget(PatientInfoScreen(name='patient_info_screen'))
        sm.add_widget(SiemensScreen1(name='siemens_screen_1'))
        sm.add_widget(SiemensScreen2(name='siemens_screen_2'))
        sm.add_widget(SiemensScreen3(name='siemens_screen_3'))
        sm.add_widget(SiemensScreen4(name='siemens_screen_4'))
        sm.add_widget(DragerScreen1(name='drager_screen_1'))
        sm.add_widget(NewMeasurementScreen(name='new_measurement_screen'))
        return sm

    def on_stop(self):
        # Liberar la cámara cuando se cierra la app
        if hasattr(self.root.get_screen('new_measurement_screen'), 'capture'):
            if self.root.get_screen('new_measurement_screen').capture.isOpened():
                self.root.get_screen('new_measurement_screen').capture.release()

class ImageButton(ButtonBehavior, Image):
    pass

if __name__ == '__main__':
    MyApp().run()