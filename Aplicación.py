from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition, SlideTransition
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.carousel import Carousel
from kivy.core.window import Window
from kivy.core.camera import Camera
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.uix.widget import Widget
from kivy.animation import Animation
import os
import cv2
import numpy as np
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle, Ellipse
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
        layout.add_widget(Label(text='Qhali Wawa', pos_hint={'center_x': 0.5, 'top': 0.9}, size_hint=(None, None), size=(Window.width, 50), color=(0, 0, 0, 1)))

        # Mensaje de error
        self.error_label = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'y': 0}, color=(1, 0, 0, 1))
        layout.add_widget(self.error_label)

        # Logo
        layout.add_widget(Image(source='logo.png', size_hint=(None, None), size=(200, 200), pos_hint={'center_x': 0.5, 'center_y': 0.7}))

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
        register_button = Button(text='¿Olvidó su contraseña?', size_hint=(0.76, None), height=44, background_normal='', pos_hint={'center_x': 0.5, 'center_y': 0.1}, background_color=(93/255, 161/255, 163/255, 1))
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
            self.manager.current = 'main_menu_screen'
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

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=70, spacing=70)

        # Botón con imagen de usuario
        self.user_button = ImageButton(source='user_icon.png', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.1, 'center_y': 1})
        self.user_button.bind(on_press=self.open_dropdown)
        layout.add_widget(self.user_button)

        # Crear el dropdown
        self.dropdown = DropDown()

        # Botón para cambiar datos
        change_password_button = Button(text='Cambiar datos', size_hint=(0.3, None), height=44, pos_hint={'center_x': 0.1, 'center_y': 0.8})
        change_password_button.bind(on_release=self.go_to_edit_data)
        self.dropdown.add_widget(change_password_button)

        # Botón para cerrar sesión
        logout_button = Button(text='Cerrar sesión', size_hint=(0.3, None), height=44, pos_hint={'center_x': 0.1, 'center_y': 0.7})
        logout_button.bind(on_release=self.logout)
        self.dropdown.add_widget(logout_button)

        # Título de bienvenida
        layout.add_widget(Label(text='¡Bienvenido! Elija un ecógrafo:', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5}, color=(0, 0, 0, 1)))

        # Layout para ecógrafos
        ecograph_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(1, 0.8))

        # Siemens
        siemens_layout = BoxLayout(orientation='vertical', size_hint=(None, None), size=(200, 200), pos_hint={'center_x': 0.5})
        siemens_layout.add_widget(Image(source="Siemens.jpg", size_hint=(None, None), size=(200, 150)))
        siemens_button = Button(text="Siemens ACUSON P500", size_hint=(None, None), size=(200, 50))
        siemens_button.bind(on_press=self.go_to_siemens_tutorial_screen)
        siemens_layout.add_widget(siemens_button)
        ecograph_layout.add_widget(siemens_layout)

        # Philips
        philips_layout = BoxLayout(orientation='vertical', size_hint=(None, None), size=(200, 200), pos_hint={'center_x': 0.5})
        philips_layout.add_widget(Image(source="Philips.jpg", size_hint=(None, None), size=(200, 150)))
        philips_button = Button(text="Philips ClearVue 550", size_hint=(None, None), size=(200, 50))
        philips_button.bind(on_press=self.go_to_philips_tutorial_screen)
        philips_layout.add_widget(philips_button)
        ecograph_layout.add_widget(philips_layout)

        layout.add_widget(ecograph_layout)
        self.add_widget(layout)

    def go_to_siemens_tutorial_screen(self, instance):
        self.manager.transition.direction = 'left'
        self.change_screen('siemens_tutorial_screen')

    def go_to_philips_tutorial_screen(self, instance):
        self.manager.transition.direction = 'left'
        self.change_screen('philips_tutorial_screen')
        
    def open_dropdown(self, instance):
        self.dropdown.open(self.user_button)

    def logout(self, instance):
        self.dropdown.dismiss()
        self.manager.transition.direction = 'right'
        self.manager.current = 'login_screen'

    def go_to_edit_data(self, instance):
        self.dropdown.dismiss()
        self.manager.transition.direction = 'left'
        self.manager.current = 'edit_data_screen'
        
    def change_screen(self, screen_name):
        self.manager.transition.direction = 'left'
        self.manager.current = screen_name

class EditDataScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout(size=Window.size)
        Window.clearcolor = (248/255, 248/255, 248/255, 1)  # Fondo #F8F8F8

        # Flecha de regreso
        back_arrow = ImageButton(source='flecha.png', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.1, 'center_y': 0.9})
        back_arrow.bind(on_press=self.go_to_main_menu_screen)
        layout.add_widget(back_arrow)

        # Título cambiar datos
        layout.add_widget(Label(text='Cambiar Datos', size_hint=(None, None), size=(Window.width, 50), pos_hint={'center_x': 0.5, 'center_y': 0.9}, color=(0, 0, 0, 1)))
        
        # Logo
        layout.add_widget(Image(source='logo.png', size_hint=(None, None), size=(130, 130), pos_hint={'center_x': 0.5, 'center_y': 0.76}))

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

        # Botón de guardar
        save_button = Button(text="Guardar", size_hint=(0.76, None), height=44, pos_hint={'center_x': 0.5, 'center_y': 0.2}, background_normal='', background_color = (93/255, 161/255, 163/255, 1))  # Botón con fondo #8FC5AB
        save_button.bind(on_press=self.save_changes)
        layout.add_widget(save_button)

        # Error repetir contraseña
        self.error_confirm_password = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'y': 0.1}, color=(1, 0, 0, 1))  # Color del mensaje de error rojo
        layout.add_widget(self.error_confirm_password)

        self.add_widget(layout)
        self.error = [0]*5
        
    def on_pre_enter(self):
        # Rellenar campos con datos actuales del usuario
        self.current_user = self.manager.database[-1]
        self.current_user[4:6] = list(map(int, self.current_user[4:6]))
        self.name_input.text = current_user[0]
        self.email.text = current_user[1]
        self.password.text = current_user[2]
        self.confirm_password.text = current_user[2]

    def data_changed(self):
        name = self.name_input.text
        email = self.email.text
        password = self.password.text
        confirm_password = self.confirm_password.text
        return name != self.manager.database[-1][0] or email != self.manager.database[-1][1] or password == self.manager.database[-1][2] or confirm_password == self.manager.database[-1][2]
    
    def show_return_popup(self, instance):
        if self.data_changed():
            box = FloatLayout()
            label_1 = Label(text='¿Está seguro de que desea regresar?', size_hint=(1, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.75})
            label_2 = Label(text='Los cambios no se guardarán.', size_hint=(1, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.55})
            return_button = Button(text='Regresar', size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5, 'y': 0.1})
            box.add_widget(return_button)
            box.add_widget(label_1)
            box.add_widget(label_2)
            self.popup = Popup(title='Regresar', content=box, size_hint=(None, None), size=(400, 200))
            return_button.bind(on_press=self.go_to_change_password_screen_1)
            self.popup.open()
        else:
            self.go_to_main_menu_screen()

    def go_to_main_menu_screen(self, instance):
        self.clear_fields()
        self.manager.transition.direction = 'right'
        self.manager.current = 'main_menu_screen'

    def clear_fields(self):
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
        
    def toggle_password_visibility(self, instance):
        if self.password.password:
            self.password.password = False
            self.show_password_button.text = 'Ocultar'
            self.confirm_password.password = False
        else:
            self.password.password = True
            self.show_password_button.text = 'Mostrar'
            self.confirm_password.password = True
        
    def save_changes(self, instance):
        if self.data_changed():
            name = self.name_input.text
            email = self.email.text
            password = self.password.text
            confirm_password = self.confirm_password.text

            errors, error_messages = self.manager.validate_fields(name, email, password, confirm_password)

            self.error_name.text = error_messages[0]
            self.error_email.text = error_messages[1]
            self.error_password.text = error_messages[2]
            self.error_confirm_password.text = error_messages[3]

            if not any(errors):
                self.clear_fields()
                self.manager.sheet.delete_rows(len(self.manager.database)+1)
                self.manager.sheet.append_row(self.current_user)
                self.manager.sheet.append_row([name, email, password, None, 1, 1])
                self.manager.database = self.manager.sheet.get_all_values()
                self.manager.database.pop(0)
                self.manager.type = 'edit_data'
                self.manager.transition.direction = 'left'
                self.manager.current = 'two_step_verification_screen'


class CircularButton(ButtonBehavior, Widget):
    def __init__(self, carousel, index, nav_buttons, **kwargs):
        super().__init__(**kwargs)
        self.carousel = carousel
        self.index = index
        self.nav_buttons = nav_buttons
        self.active_color = (93 / 255, 161 / 255, 163 / 255, 1)  # Color celeste
        self.inactive_color = (0.5, 0.5, 0.5, 1)  # Color gris claro
        with self.canvas:
            self.circle_color = Color(*self.inactive_color)  # Color inicial
            self.circle = Ellipse(size=(20, 20), pos=self.pos)
        self.bind(pos=self.update_circle, size=self.update_circle)
        self.bind(on_press=self.on_button_press)

    def update_circle(self, *args):
        self.circle.pos = self.center_x - self.circle.size[0] / 2, self.center_y - self.circle.size[1] / 2

    def on_button_press(self, *args):
        self.carousel.load_slide(self.carousel.slides[self.index])  # Deslizar a la página correspondiente
        self.update_circular_buttons()

    def set_active(self, active):
        if active:
            self.circle_color.rgba = self.active_color
        else:
            self.circle_color.rgba = self.inactive_color

    def update_circular_buttons(self):
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == self.index)

class SiemensTutorialScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        # Flecha de regreso
        back_arrow = ImageButton(source='flecha.png', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.1, 'center_y': 0.9})
        back_arrow.bind(on_press=self.go_to_main_menu_screen)
        layout.add_widget(back_arrow)

        # Crear el Carousel
        self.carousel = Carousel(direction='right', loop=False)

        # Diapositiva 1
        slide1 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title1 = Label(text='Tutorial\nEncendido del Ecógrafo e Inicio de Sesión', size_hint=(1, None), height=50, font_size='20sp', halign='center', color=(0, 0, 0, 1))
        title1.bind(size=title1.setter('text_size'))
        slide1.add_widget(title1)
        slide1.add_widget(Image(source='Siemens - botón de encendido.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5}))
        description1 = Label(text='Presione el botón de encendido. \nPara iniciar sesión, escriba "admin" en user y haga click izquierdo en el botón "ok".', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), font_size='16sp', color=(0, 0, 0, 1))
        description1.bind(size=description1.setter('text_size'))
        slide1.add_widget(description1)
        self.carousel.add_widget(slide1)

        # Diapositiva 2
        slide2 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title2 = Label(text='Tutorial\nRegistro del Paciente', size_hint=(1, None), height=50, font_size='20sp', halign='center', color=(0, 0, 0, 1))
        title2.bind(size=title2.setter('text_size'))
        slide2.add_widget(title2)
        slide2.add_widget(Image(source='Siemens - botón de patient.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5}))
        description2 = Label(text='Presione el botón "Patient" y registre los datos del paciente, luego haga click en el botón "ok".', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), font_size='16sp', color=(0, 0, 0, 1))
        description2.bind(size=description2.setter('text_size'))
        slide2.add_widget(description2)
        self.carousel.add_widget(slide2)

        # Diapositiva 3
        slide3 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title3 = Label(text='Tutorial\nSelección de Preajuste', size_hint=(1, None), height=50, font_size='20sp', halign='center', color=(0, 0, 0, 1))
        title3.bind(size=title3.setter('text_size'))
        slide3.add_widget(title3)
        slide3.add_widget(Image(source='Siemens - botón de exam.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5}))
        description3 = Label(text='Presione el botón "Exam" y elija el preajuste adecuado.', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), font_size='16sp', color=(0, 0, 0, 1))
        description3.bind(size=description3.setter('text_size'))
        slide3.add_widget(description3)
        self.carousel.add_widget(slide3)

        # Diapositiva 4
        slide4 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title4 = Label(text='Tutorial\nAutoajuste', size_hint=(1, None), height=50, font_size='20sp', halign='center', color=(0, 0, 0, 1))
        title4.bind(size=title4.setter('text_size'))
        slide4.add_widget(title4)
        slide4.add_widget(Image(source='Siemens - botón de autoset.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5}))
        description4 = Label(text='Presione este botón para ajustar automáticamente la imagen ecográfica.', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), font_size='16sp', color=(0, 0, 0, 1))
        description4.bind(size=description4.setter('text_size'))
        slide4.add_widget(description4)
        self.carousel.add_widget(slide4)

        # Diapositiva 5
        slide5 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title5 = Label(text='Tutorial\nColocación de la Cinta Verde', size_hint=(1, None), height=50, font_size='20sp', halign='center', color=(0, 0, 0, 1))
        title5.bind(size=title5.setter('text_size'))
        slide5.add_widget(title5)
        slide5.add_widget(Image(source='Abdomen con cinta verde.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5}))
        description5 = Label(text='Coloque la cinta verde como se ve en la imagen.\n¡Ahora está listo(a) para realizar la ecografía!', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), font_size='16sp', color=(0, 0, 0, 1))
        description5.bind(size=description5.setter('text_size'))
        slide5.add_widget(description5)
        # Botón para la siguiente instrucción
        start_measurement_button = Button(text="Iniciar Medición", size_hint=(None, None), width=200, height=40, pos_hint={'center_x': 0.5, 'center_y': 0.1})
        start_measurement_button.bind(on_press=self.show_instruction_popup)
        slide5.add_widget(start_measurement_button)
        self.carousel.add_widget(slide5)

        layout.add_widget(self.carousel)

        # Crear botones circulares para la navegación
        self.nav_layout = BoxLayout(orientation='horizontal', size_hint=(None, None), height=50, width=200, spacing=20, pos_hint={'center_x': 0.5})
        self.nav_buttons = []
        for i in range(len(self.carousel.slides)):  # Create buttons based on the number of slides
            btn = CircularButton(carousel=self.carousel, index=i, nav_buttons=self.nav_buttons)
            self.nav_buttons.append(btn)
            self.nav_layout.add_widget(btn)

        layout.add_widget(self.nav_layout)

        self.carousel.bind(index=self.update_circular_buttons)
        
        self.add_widget(layout)

    def on_enter(self, *args):
        # Activar el primer botón circular al ingresar al tutorial
        self.update_circular_buttons(self.carousel, self.carousel.index)

    def update_circular_buttons(self, instance, value):
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == value)

    def on_index_change(self, instance, value):
        print(1)
        self.update_circular_buttons(instance, value)

    def go_to_main_menu_screen(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'main_menu_screen'
            
    def show_instruction_popup(self, instance):
        box_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        box_layout.add_widget(Label(text="Coloque el celular en el visor y ajústelo."))
        
        accept_button = Button(text="Continuar", size_hint=(1, 0.4))
        accept_button.bind(on_press=self.proceed_to_measurement)
        box_layout.add_widget(accept_button)

        self.popup = Popup(title="Instrucción de la Colocación del celular", content=box_layout, size_hint=(None, None), size=(400, 200), auto_dismiss=False)

        self.popup.open()

    def proceed_to_measurement(self, instance):
        self.popup.dismiss()
        self.manager.transition.direction = 'left'
        self.manager.current = 'new_measurement_screen'

    def on_leave(self, *args):
        # Reset carousel to the first slide
        self.carousel.index = 0
        self.update_circular_buttons(self.carousel, 0)

# Pantalla para el ecógrafo Philips
class PhilipsTutorialScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        # Flecha de regreso
        back_arrow = ImageButton(source='flecha.png', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.1, 'center_y': 0.9})
        back_arrow.bind(on_press=self.go_to_main_menu_screen)
        layout.add_widget(back_arrow)

        # Crear el Carousel
        self.carousel = Carousel(direction='right', loop=False)
        self.carousel.bind(on_index=self.update_circular_buttons)

        # Diapositiva 1
        slide1 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title1 = Label(text='Tutorial\nEncendido del Ecógrafo e Inicio de Sesión', size_hint=(1, None), height=50, font_size='20sp', halign='center', color=(0, 0, 0, 1))
        title1.bind(size=title1.setter('text_size'))
        slide1.add_widget(title1)
        slide1.add_widget(Image(source='Philips - botón de encendido.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5}))
        description1 = Label(text='Presione el botón de encendido que se encuentra en la esquina superior izquierda del panel de control.', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), font_size='16sp', color=(0, 0, 0, 1))
        description1.bind(size=description1.setter('text_size'))
        slide1.add_widget(description1)
        self.carousel.add_widget(slide1)

        # Diapositiva 2
        slide2 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title2 = Label(text='Tutorial\nRegistro del Paciente', size_hint=(1, None), height=50, font_size='20sp', halign='center', color=(0, 0, 0, 1))
        title2.bind(size=title2.setter('text_size'))
        slide2.add_widget(title2)
        slide2.add_widget(Image(source='Philips - botón de patient.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5}))
        description2 = Label(text='Presione el botón "Patient" y registre los datos del paciente, luego haga click en el botón "ok".', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), font_size='16sp', color=(0, 0, 0, 1))
        description2.bind(size=description2.setter('text_size'))
        slide2.add_widget(description2)
        self.carousel.add_widget(slide2)

        # Diapositiva 3
        slide3 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title3 = Label(text='Tutorial\nSelección de Preajuste', size_hint=(1, None), height=50, font_size='20sp', halign='center', color=(0, 0, 0, 1))
        title3.bind(size=title3.setter('text_size'))
        slide3.add_widget(title3)
        slide3.add_widget(Image(source='Philips - botón de preset.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5}))
        description3 = Label(text='Presione el botón "Preset" y elija el preajuste adecuado.', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), font_size='16sp', color=(0, 0, 0, 1))
        description3.bind(size=description3.setter('text_size'))
        slide3.add_widget(description3)
        self.carousel.add_widget(slide3)

        # Diapositiva 4
        slide4 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title4 = Label(text='Tutorial\nAutoajuste', size_hint=(1, None), height=50, font_size='20sp', halign='center', color=(0, 0, 0, 1))
        title4.bind(size=title4.setter('text_size'))
        slide4.add_widget(title4)
        slide4.add_widget(Image(source='Philips - botón de iSCAN.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5}))
        description4 = Label(text='Presione el botón de iSCAN para ajustar automáticamente la imagen ecográfica.\n¡Ahora está listo(a) para realizar la ecografía!', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), font_size='16sp', color=(0, 0, 0, 1))
        description4.bind(size=description4.setter('text_size'))
        slide4.add_widget(description4)
        # Botón para la siguiente instrucción
        start_measurement_button = Button(text="Iniciar Medición", size_hint=(None, None), width=200, height=40, pos_hint={'center_x': 0.5, 'center_y': 0.1})
        start_measurement_button.bind(on_press=self.show_instruction_popup)
        slide4.add_widget(start_measurement_button)
        self.carousel.add_widget(slide4)

        # Diapositiva 5
        slide5 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title5 = Label(text='Tutorial\nColocación de la Cinta Verde', size_hint=(1, None), height=50, font_size='20sp', halign='center', color=(0, 0, 0, 1))
        title5.bind(size=title5.setter('text_size'))
        slide5.add_widget(title5)
        slide5.add_widget(Image(source='Abdomen con cinta verde.png', size_hint=(None, None), size=(600, 400), pos_hint={'center_x': 0.5}))
        description5 = Label(text='Coloque la cinta verde como se ve en la imagen.\n¡Ahora está listo(a) para realizar la ecografía!', size_hint=(1, None), halign='center', valign='middle', text_size=(self.width - 20, None), font_size='16sp', color=(0, 0, 0, 1))
        description5.bind(size=description5.setter('text_size'))
        slide5.add_widget(description5)
        # Botón para la siguiente instrucción
        start_measurement_button = Button(text="Iniciar Medición", size_hint=(None, None), width=200, height=40, pos_hint={'center_x': 0.5, 'center_y': 0.1})
        start_measurement_button.bind(on_press=self.show_instruction_popup)
        slide5.add_widget(start_measurement_button)
        self.carousel.add_widget(slide5)

        layout.add_widget(self.carousel)

        # Crear botones circulares para la navegación
        self.nav_layout = BoxLayout(orientation='horizontal', size_hint=(None, None), height=50, width=200, spacing=20, pos_hint={'center_x': 0.5})
        self.nav_buttons = []
        for i in range(len(self.carousel.slides)):
            btn = CircularButton(carousel=self.carousel, index=i, nav_buttons=self.nav_buttons)
            self.nav_buttons.append(btn)
            self.nav_layout.add_widget(btn)
        layout.add_widget(self.nav_layout)

        self.add_widget(layout)

    def on_enter(self, *args):
        # Activar el primer botón circular al ingresar al tutorial
        self.update_circular_buttons(self.carousel, self.carousel.index)

    def update_circular_buttons(self, instance, value):
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == value)

    def go_to_main_menu_screen(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'main_menu_screen'
            
    def show_instruction_popup(self, instance):
        box_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        box_layout.add_widget(Label(text="Coloque el celular en el visor y ajústelo."))
        
        accept_button = Button(text="Continuar", size_hint=(1, 0.4))
        accept_button.bind(on_press=self.proceed_to_measurement)
        box_layout.add_widget(accept_button)

        self.popup = Popup(title="Instrucción de la Colocación del celular", content=box_layout, size_hint=(None, None), size=(400, 200), auto_dismiss=False)

        self.popup.open()

    def proceed_to_measurement(self, instance):
        self.popup.dismiss()
        self.manager.transition.direction = 'left'
        self.manager.current = 'new_measurement_screen'

    def on_leave(self, *args):
        # Reset carousel to the first slide
        self.carousel.index = 0
        self.update_circular_buttons(self.carousel, 0)

class NewMeasurementScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        # Flecha de regreso
        back_arrow = ImageButton(source='flecha.png', size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.1, 'center_y': 0.9})
        back_arrow.bind(on_press=self.go_to_main_menu_screen)
        self.layout.add_widget(back_arrow)
        
        self.camera_widget = Image(size_hint=(1, 0.9))
        self.layout.add_widget(self.camera_widget)

        self.camera_button = Button(text="Prender Cámara", size_hint=(1, 0.1))
        self.camera_button.bind(on_press=self.toggle_camera)
        self.layout.add_widget(self.camera_button)

        self.add_widget(self.layout)
        
        self.capture = None

        # Rangos HSV para el color verde fosforescente
        self.verdeBajo = np.array([35, 100, 100], np.uint8)
        self.verdeAlto = np.array([85, 255, 255], np.uint8)

        # Estado para controlar el modo de visualización
        self.modo_visualizacion = 0  # Inicialización del modo de visualización

        # Función para manejar los clics del mouse
        def on_click(x, y, button, pressed):
            if pressed:
                self.modo_visualizacion = (self.modo_visualizacion + 1) % 14  # Ciclar entre 0 y 13

        # Iniciar el oyente del mouse en un hilo aparte
        from pynput.mouse import Listener as MouseListener
        listener = MouseListener(on_click=on_click)
        listener.start()

    def go_to_main_menu_screen(self, instance):
        if self.capture is not None:
            if self.capture.isOpened():
                self.capture.release()
                self.capture = None
                self.camera_button.text = "Prender Cámara"
                self.camera_widget.texture = None
        self.manager.transition.direction = 'right'
        self.manager.current = 'main_menu_screen'
    
    def toggle_camera(self, *args):
        if self.capture is None:
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.CAMERA])
            self.capture = cv2.VideoCapture(0)
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
        layout.add_widget(Label(text='Registro', size_hint=(None, None), size=(Window.width, 50), pos_hint={'center_x': 0.5, 'center_y': 0.9}, color=(0, 0, 0, 1)))
        
        # Logo
        layout.add_widget(Image(source='logo.png', size_hint=(None, None), size=(130, 130), pos_hint={'center_x': 0.5, 'center_y': 0.76}))
        
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
        
    def clear_fields(self, instance):
        self.name_input.text = ''
        self.email.text = ''
        self.password.text = ''
        self.confirm_password.text = ''
        self.error_name.text = ''
        self.error_email.text = ''
        self.error_password.text = ''
        self.error_confirm_password.text = ''
        
    def go_to_login(self, instance):
        self.password.password = True
        self.show_password_button.text = 'Mostrar'
        self.show_password_button.state = 'normal'
        if self.popup:
            self.popup.dismiss()
        self.manager.transition.direction = 'right'
        self.manager.current = 'login_screen'
        
    def save_to_database(self, instance):
        name = self.name_input.text
        email = self.email.text
        password = self.password.text
        confirm_password = self.confirm_password.text

        errors, error_messages = self.manager.validate_fields(name, email, password, confirm_password)

        if (email != current_email) and (email in list(map(lambda Usuario: Usuario[1], self.database))):
            self.show_email_already_registered_popup()
        else:
            self.error_name.text = error_messages[0]
            self.error_email.text = error_messages[1]
            self.error_password.text = error_messages[2]
            self.error_confirm_password.text = error_messages[3]

        if not any(errors):
            self.manager.sheet.append_row([name, email, password, None, 1, 1])
            self.manager.database = self.manager.sheet.get_all_values()
            self.manager.database.pop(0)
            self.clear_fields()
            self.password.password = True
            self.show_password_button.text = 'Mostrar'
            self.show_password_button.state = 'normal'
            self.manager.type = 'register'
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
        layout.add_widget(Label(text='Cambiar Contraseña', size_hint=(None, None), size=(Window.width, 50), pos_hint={'center_x': 0.5, 'center_y': 0.9}, color=(0, 0, 0, 1)))
        
        # Logo
        layout.add_widget(Image(source='logo.png', size_hint=(None, None), size=(130, 130), pos_hint={'center_x': 0.5, 'center_y': 0.76}))

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
            self.manager.type = 'change_password'
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
        layout.add_widget(Label(text='Cambiar Contraseña', size_hint=(None, None), size=(Window.width, 50), pos_hint={'center_x': 0.5, 'center_y': 0.9}, color=(0, 0, 0, 1)))
        
        # Logo
        layout.add_widget(Image(source='logo.png', size_hint=(None, None), size=(130, 130), pos_hint={'center_x': 0.5, 'center_y': 0.76}))
        
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

        errors, error_messages = self.manager.validate_fields(self.manager.database[-1][0], self.manager.database[-1][1], password, confirm_password)
        
        self.error_password.text = error_messages[2]
        self.error_confirm_password.text = error_messages[3]
        
        if not any(self.error[2:4]):
            if password == self.manager.database[-1][2]:
                self.error_confirm_password.text = 'Esta contraseña ya ha sido utilizada anteriormente.'
            else:
                self.password.text = ''
                self.error_password.text = ''
                self.confirm_password.text = ''
                self.error_confirm_password.text = ''
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
        layout.add_widget(Label(text='Verificación en 2 Pasos', size_hint=(None, None), size=(Window.width, 50), pos_hint={'center_x': 0.5, 'center_y': 0.9}, color=(0, 0, 0, 1)))
        
        # Logo
        layout.add_widget(Image(source='logo.png', size_hint=(None, None), size=(130, 130), pos_hint={'center_x': 0.5, 'center_y': 0.76}))
        
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
        self.error = Label(text='', size_hint=(None, None), size=(300, 44), pos_hint={'center_x': 0.5, 'y': 0.25}, color=(1, 0, 0, 1))  # Color del mensaje de error rojo
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
        if self.manager.type == 'register' or self.manager.type == 'edit_data':
            self.manager.sheet.delete_rows(len(self.manager.database)+1)
            self.manager.database = self.manager.sheet.get_all_values()
            self.manager.database.pop(0)
            self.manager.current = self.manager.type+'_screen'
        elif self.manager.type == 'change_password':
            self.manager.current = self.manager.type+'_screen_1'
        
    def validate_code(self, instance):
        if self.verification_code_input.text == self.verification_code:
            Clock.unschedule(self.new_code_event)
            self.verification_code_input.text = ''
            self.error.text = ''
            self.manager.sheet.update([[1]], f'E{len(self.manager.database)+1}')
            if self.manager.type == 'register' or self.manager.type == 'edit_data':
                if self.manager.type == 'edit_data':
                    self.manager.sheet.delete_rows(len(self.manager.database))
                self.manager.database = self.manager.sheet.get_all_values()
                self.manager.database.pop(0)
                box = FloatLayout()
                label = Label(text='', size_hint=(1.2, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.7})
                button = Button(text='Acceder', size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5, 'y': 0.1})
                box.add_widget(button)
                button.bind(on_press=self.go_to_main_menu_screen)
                self.popup = Popup(title='Éxito', content=box, size_hint=(None, None), size=(400, 200))
                box.add_widget(label)
                if self.manager.type == 'register':
                    label.text = '¡Sus datos fueron agregados a la base de datos!'
                else:
                    label.text = '¡Sus datos fueron actualizados en la base de datos!'
                self.popup.open()
            elif self.manager.type == 'change_password':
                self.manager.current = 'change_password_screen_2'
        else:
            self.error.text = 'Código de verificación incorrecto'

    def go_to_main_menu_screen(self, instance):
        self.verification_code_input.text = ''
        self.error.text = ''
        self.popup.dismiss()
        self.manager.transition.direction = 'left'
        self.manager.current = 'main_menu_screen'
            
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

    def validate_fields(self, name, email, password, confirm_password):
        errors = [0]*4
        error_messages = ['']*4
        
        if not ''.join(name.split()).isalpha():
            errors[0] = 1
            error_messages[0] = 'El nombre solo puede contener letras y espacios.'
        
        if (not email.replace('.', '').replace('@', '', 1).isalnum()) or ('@' not in email) or ('.' not in email):
            errors[1] = 1
            error_messages[1] = 'Correo electrónico inválido.'
        
        if (len(password)<10) or (not any(list(map(lambda Carácter: Carácter.isupper(), list(password))))) or (not any(list(map(lambda Carácter: Carácter.islower(), list(password))))) or (not any(list(map(lambda Carácter: Carácter.isnumeric(), list(password))))):
            errors[2] = 1
            error_messages[2] = 'La contraseña debe tener al menos 10 caracteres y debe contener mayúsculas, minúsculas y números.'
        
        if password != confirm_password:
            errors[3] = 1
            error_messages[3] = 'Las contraseñas no coinciden.'
        
        return errors, error_messages

    def on_back_button(self, window, key, *args):
        if key == 27: # 27 is the key code for the back button on Android
            current_screen = self.current
            if current_screen == 'register_screen':
                self.get_screen('register_screen').go_to_login(None)
                return True
            elif current_screen == 'change_password_screen_1':
                self.get_screen('change_password_screen_1').go_to_login(None)
                return True
            elif current_screen == 'two_step_verification_screen':
                self.get_screen('two_step_verification_screen').show_return_popup(None)
                return True
            elif current_screen == 'change_password_screen_2':
                self.get_screen('change_password_screen_2').show_return_popup(None)
                return True
            elif current_screen == 'edit_data_screen':
                self.get_screen('main_menu_screen').show_return_popup(None)
                return True
            elif current_screen == 'siemens_tutorial screen':
                self.get_screen('main_menu_screen').go_to_main_menu(None)
                return True
            elif current_screen == 'philips_tutorial_screen':
                self.get_screen('main_menu_screen').go_to_main_menu(None)
                return True
        return False

class ImageButton(ButtonBehavior, Image):
    pass

class MyApp(App):
    def build(self):
        sm = MyScreenManager(transition=SlideTransition())
        sm.add_widget(LoginScreen(name='login_screen'))
        sm.add_widget(RegisterScreen(name='register_screen'))
        sm.add_widget(ChangePasswordScreen1(name='change_password_screen_1'))
        sm.add_widget(ChangePasswordScreen2(name='change_password_screen_2'))
        sm.add_widget(TwoStepVerificationScreen(name='two_step_verification_screen'))
        sm.add_widget(MainMenuScreen(name='main_menu_screen'))
        sm.add_widget(EditDataScreen(name='edit_data_screen'))
        sm.add_widget(SiemensTutorialScreen(name='siemens_tutorial_screen'))
        sm.add_widget(PhilipsTutorialScreen(name='philips_tutorial_screen'))
        sm.add_widget(NewMeasurementScreen(name='new_measurement_screen'))
        return sm
            
if __name__ == '__main__':
    MyApp().run()
