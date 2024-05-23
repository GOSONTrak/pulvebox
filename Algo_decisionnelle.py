import sys
import time
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar,
                               QLCDNumber, QSlider)
from PySide6.QtCore import Qt, QTimer


class DecisionAlgorithme:
    TIME = time.monotonic()

    def __init__(self, state_care: bool = False, mission_time: float = 1050.0,
                 quantity_produced_1=2000.0, quantity_produced_2=2000.0, quantity_produced_3=2000.0,
                 mixer_volume_0=3000.0, output_flow=50.0):

        self.state_care = state_care
        self.mission_time = mission_time
        self.remaining_time = mission_time
        self.departure_time = time.monotonic()

        self.quantity_produced_1 = quantity_produced_1
        self.quantity_produced_2 = quantity_produced_2
        self.quantity_produced_3 = quantity_produced_3
        self.mixer_volume_0 = mixer_volume_0
        self.output_flow = output_flow

        self.mixer_state = False
        self.current_volume = self.mixer_volume_0

    def decision(self):
        dt = (time.monotonic() - self.departure_time)
        self.remaining_time = self.mission_time - dt
        if self.state_care and self.remaining_time > 0:
            self.get_current_volume()
            if self.current_volume <= self.mixer_volume_0 / 2 and dt < self.remaining_time / 2:
                print(" volume courant", self.current_volume)
                self.replenish_mixer()
                self.mixer_state = True
                time.sleep(2)
            else:
                self.mixer_state = False
        else:
            self.mixer_state = False
            raise Exception(" the care is off !")

    def get_current_volume(self):
        self.current_volume = self.mixer_volume_0 - self.output_flow * (time.monotonic() - self.TIME)
        if self.current_volume < 0:
            self.current_volume = 0

    def replenish_mixer(self):
        self.quantity_produced_1 -= self.current_volume / 3
        self.quantity_produced_2 -= self.current_volume / 3
        self.quantity_produced_3 -= self.current_volume / 3
        self.current_volume += self.mixer_volume_0 / 2
        self.check_quantity()
        self.TIME = time.monotonic()

    def check_quantity(self):
        if min(self.quantity_produced_1, self.quantity_produced_2, self.quantity_produced_3) < 0:
            raise Exception("All produced quantities are finished")

    def update_mission_time(self, new_time):
        self.mission_time = new_time
        self.remaining_time = new_time
        self.departure_time = time.monotonic()

    def update_output_flow(self, new_flow):
        self.output_flow = new_flow

    def reset(self):
        self.remaining_time = self.mission_time
        self.current_volume = self.mixer_volume_0
        self.mixer_state = False
        self.departure_time = time.monotonic()


class Application(QWidget):
    def __init__(self, decision_algorithm):
        super().__init__()
        self.decision_algorithm = decision_algorithm

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_interface)

    def init_ui(self):
        self.setWindowTitle('Evolution des Paramètres dans le Temps')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        title = QLabel("Suivi de la Production en Temps Réel")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")

        self.led = QLabel()
        self.led.setFixedSize(20, 20)
        self.led.setStyleSheet("background-color: red; border-radius: 10px;")

        self.labels = {
            "mixer_state": QLabel("État du Mélangeur:"),
            "current_volume": QLabel("Volume Actuel:"),
            "quantity_produced_1": QLabel("Quantité Produite 1:"),
            "quantity_produced_2": QLabel("Quantité Produite 2:"),
            "quantity_produced_3": QLabel("Quantité Produite 3:"),
            "remaining_time": QLabel("Temps Restant:"),
            "output_flow": QLabel("Débit de Sortie:")
        }

        self.values = {
            "mixer_state": QLabel(""),
            "current_volume": QLabel(""),
            "quantity_produced_1": QLabel(""),
            "quantity_produced_2": QLabel(""),
            "quantity_produced_3": QLabel(""),
            "remaining_time": QLabel(""),
            "output_flow": QLabel("")
        }

        layout.addWidget(title)

        h_layout_info = QHBoxLayout()
        info_layout = QVBoxLayout()
        for key, label in self.labels.items():
            h_layout = QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(self.values[key])
            info_layout.addLayout(h_layout)

        h_layout_led = QHBoxLayout()
        h_layout_led.addWidget(QLabel("LED du Mélangeur:"))
        h_layout_led.addWidget(self.led)

        info_layout.addLayout(h_layout_led)
        h_layout_info.addLayout(info_layout)

        self.progress = QProgressBar()
        self.progress.setMaximum(self.decision_algorithm.mission_time)
        self.progress.setValue(self.decision_algorithm.mission_time)

        self.lcd = QLCDNumber()
        self.lcd.setDigitCount(8)
        self.lcd.display("00:00:00")

        self.slider_mission_time = QSlider(Qt.Horizontal)
        self.slider_mission_time.setMinimum(300)
        self.slider_mission_time.setMaximum(3600)
        self.slider_mission_time.setValue(self.decision_algorithm.mission_time)
        self.slider_mission_time.valueChanged.connect(self.update_mission_time)

        self.slider_output_flow = QSlider(Qt.Horizontal)
        self.slider_output_flow.setMinimum(10)
        self.slider_output_flow.setMaximum(100)
        self.slider_output_flow.setValue(self.decision_algorithm.output_flow)
        self.slider_output_flow.valueChanged.connect(self.update_output_flow)

        self.start_button = QPushButton('Démarrer')
        self.stop_button = QPushButton('Arrêter')
        self.start_button.clicked.connect(self.start_algorithm)
        self.stop_button.clicked.connect(self.stop_algorithm)

        h_layout_buttons = QHBoxLayout()
        h_layout_buttons.addWidget(self.start_button)
        h_layout_buttons.addWidget(self.stop_button)

        layout.addLayout(h_layout_info)
        layout.addWidget(self.progress)
        layout.addWidget(self.lcd)

        h_layout_slider_mission_time = QHBoxLayout()
        h_layout_slider_mission_time.addWidget(QLabel("Ajuster le Temps de Mission:"))
        h_layout_slider_mission_time.addWidget(self.slider_mission_time)

        h_layout_slider_output_flow = QHBoxLayout()
        h_layout_slider_output_flow.addWidget(QLabel("Ajuster le Débit de Sortie:"))
        h_layout_slider_output_flow.addWidget(self.slider_output_flow)

        # Barres de progression verticales
        self.progress_1 = QProgressBar()
        self.progress_1.setOrientation(Qt.Vertical)
        self.progress_1.setStyleSheet("QProgressBar::chunk {background-color: red;}")
        self.progress_1.setMaximum(self.decision_algorithm.quantity_produced_1)
        self.progress_1.setValue(self.decision_algorithm.quantity_produced_1)

        self.progress_2 = QProgressBar()
        self.progress_2.setOrientation(Qt.Vertical)
        self.progress_2.setStyleSheet("QProgressBar::chunk {background-color: green;}")
        self.progress_2.setMaximum(self.decision_algorithm.quantity_produced_2)
        self.progress_2.setValue(self.decision_algorithm.quantity_produced_2)

        self.progress_3 = QProgressBar()
        self.progress_3.setOrientation(Qt.Vertical)
        self.progress_3.setStyleSheet("QProgressBar::chunk {background-color: blue;}")
        self.progress_3.setMaximum(self.decision_algorithm.quantity_produced_3)
        self.progress_3.setValue(self.decision_algorithm.quantity_produced_3)

        h_layout_progress_bars = QHBoxLayout()
        h_layout_progress_bars.addWidget(QLabel("Produit 1"))
        h_layout_progress_bars.addWidget(self.progress_1)
        h_layout_progress_bars.addWidget(QLabel("Produit 2"))
        h_layout_progress_bars.addWidget(self.progress_2)
        h_layout_progress_bars.addWidget(QLabel("Produit 3"))
        h_layout_progress_bars.addWidget(self.progress_3)

        layout.addLayout(h_layout_slider_mission_time)
        layout.addLayout(h_layout_slider_output_flow)
        layout.addLayout(h_layout_progress_bars)
        layout.addLayout(h_layout_buttons)

        self.setLayout(layout)

    def update_interface(self):
        if self.decision_algorithm.state_care:
            try:
                self.decision_algorithm.decision()
            except Exception as e:
                print(e)
                self.stop_algorithm()

            elapsed_time = self.decision_algorithm.mission_time - self.decision_algorithm.remaining_time
            self.progress.setMaximum(self.decision_algorithm.mission_time)
            self.progress.setValue(self.decision_algorithm.remaining_time)

            hours, rem = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(rem, 60)
            self.lcd.display(f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}")

            if self.decision_algorithm.mixer_state:
                self.led.setStyleSheet("background-color: green; border-radius: 10px;")
            else:
                self.led.setStyleSheet("background-color: red; border-radius: 10px;")

            self.progress_1.setValue(self.decision_algorithm.quantity_produced_1)
            self.progress_2.setValue(self.decision_algorithm.quantity_produced_2)
            self.progress_3.setValue(self.decision_algorithm.quantity_produced_3)

    def start_algorithm(self):
        self.decision_algorithm.state_care = True
        self.decision_algorithm.reset()
        self.timer.start(1000)

    def stop_algorithm(self):
        self.decision_algorithm.state_care = False
        self.timer.stop()

    def update_mission_time(self, value):
        self.decision_algorithm.update_mission_time(value)
        self.progress.setMaximum(value)

    def update_output_flow(self, value):
        self.decision_algorithm.update_output_flow(value)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    decision_algorithm = DecisionAlgorithme(state_care=False)
    application = Application(decision_algorithm)
    application.show()

    sys.exit(app.exec())
