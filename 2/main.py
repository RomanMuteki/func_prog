import cv2
import multiprocessing as multiprocessing
import numpy as np
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox


def analyzePart(arguments):
    photoPart, partIndex, photoName, offsetX, offsetY = arguments

    grayphoto = cv2.cvtColor(photoPart, cv2.COLOR_BGR2GRAY)
    blurredphoto = cv2.GaussianBlur(grayphoto, (3, 3), 0)
    _, binaryphoto = cv2.threshold(blurredphoto, 160, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binaryphoto, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    objectsData = []
    contourCenters = []

    for contour in contours:
        contourArea = cv2.contourArea(contour)
        x, y, contourWidth, contourHeight = cv2.boundingRect(contour)
        centerX = x + contourWidth // 2 + offsetX
        centerY = y + contourHeight // 2 + offsetY

        brightness = np.sum(grayphoto[y:y + contourHeight, x:x + contourWidth])
        objectType = classification(contourArea, brightness)

        if objectType != "-":
            objectsData.append({
                "photo": photoName,
                "partIndex": partIndex + 1,
                "coordinates": (centerX, centerY),
                "brightness": brightness,
                "area": int(contourArea),
                "type": objectType
            })

            contourCenters.append(
                (centerX - offsetX, centerY - offsetY, max(contourWidth, contourHeight) // 2, objectType))

    return objectsData, contourCenters


def classification(area, brightness):
    if area < 100 and brightness > 200:
        return "Звезда"
    elif 300 < area < 1000 and brightness > 1000:
        return "Большая звезда"
    elif area > 1000:
        return "Галактика"
    elif area > 100 and brightness < 200:
        return "Планета"
    else:
        return "Звезда"


def processAllphotos(inputDirectory, outputXLSXPath, outputphotoDir):
    allResults = []

    for photoName in os.listdir(inputDirectory):
        photoPath = os.path.join(inputDirectory, photoName)
        if photoPath.lower().endswith(('.png', '.jpg')):
            objectsData = processphoto(photoPath, outputphotoDir)
            allResults.extend(objectsData)

    save(allResults, outputXLSXPath)
    print(f"Analysis complete. Results saved to {outputXLSXPath}")


def save(data, output_xlsx_path):
    df = pd.DataFrame(data)
    df.to_excel(output_xlsx_path, index=False)


def processphoto(photoPath, outputphotoDir):
    photo = cv2.imread(photoPath)
    photoName = os.path.basename(photoPath)

    photoOutputDir = os.path.join(outputphotoDir, os.path.splitext(photoName)[0])
    os.makedirs(photoOutputDir, exist_ok=True)

    photoParts = splitphoto(photo, 1500)


    arguments = [(part, partIndex, photoName, offsetX, offsetY)
                 for part, offsetX, offsetY, partIndex in photoParts]


    with multiprocessing.Pool(processes=8) as processPool:
        results = processPool.map(analyzePart, arguments)

    allObjectsData = []
    for objectData, contourCenters in results:
        allObjectsData.extend(objectData)

    for (part, offsetX, offsetY, partIndex), (_, contourCenters) in zip(photoParts, results):
        savephotoPart(part, partIndex, photoName, photoOutputDir, contourCenters)

    return allObjectsData


def splitphoto(photo, partSize):
    photoHeight, photoWidth, _ = photo.shape
    photoParts = []

    partIndex = 0
    for offsetY in range(0, photoHeight, partSize):
        for offsetX in range(0, photoWidth, partSize):
            part = photo[offsetY:offsetY + partSize, offsetX:offsetX + partSize]
            if part.size > 0:
                photoParts.append((part, offsetX, offsetY, partIndex))
            partIndex += 1

    return photoParts


def savephotoPart(part, partIndex, photoName, outputDir, contourCenters):
    for (centerX, centerY, radius, objectType) in contourCenters:
        largerRadius = int(radius * 1.5)

        if objectType == "Звезда":
            color = (255, 0, 0)
        elif objectType == "Планета":
            color = (0, 0, 255)
        elif objectType == "Большая звезда":
            color = (0, 255, 0)
        elif objectType == "Галактика":
            color = (255, 255, 0)
        else:
            color = (100, 100, 100)

        cv2.circle(part, (centerX, centerY), largerRadius, color, 1)

    partphotoName = f"{partIndex + 1}.png"
    partphotoPath = os.path.join(outputDir, partphotoName)
    cv2.imwrite(partphotoPath, part)


def analyze():
    global inputDirectory, outputXLSXPath, outputphotoDir
    if not inputDirectory:
        inputDirectory = 'photo'

    if not outputXLSXPath:
        outputXLSXPath = os.path.join(os.getcwd(), 'statistic.xlsx')

    outputphotoDir = 'photo_parts'
    os.makedirs(outputphotoDir, exist_ok=True)

    processAllphotos(inputDirectory, outputXLSXPath, outputphotoDir)

    messagebox.showinfo("Анализ завершен", f"Результаты сохранены в {outputXLSXPath}")


def choosephotos():
    global inputDirectory
    inputDirectory = filedialog.askdirectory()
    if inputDirectory:
        label_selected_photos.config(text=f"Выбраны изображения: {inputDirectory}")


def savePath():
    global outputXLSXPath
    output_directory = filedialog.askdirectory()
    if output_directory:
        outputXLSXPath = os.path.join(output_directory, 'statistic.xlsx')
        label_save_path.config(text=f"Сохранить в: {outputXLSXPath}")


def create_interface():
    global btn_analyze, label_selected_photos, label_save_path

    root = tk.Tk()
    root.title("Анализ космических данных")

    window_width = 600
    window_height = 120
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    label_selected_photos = tk.Label(root, text="Директория с изображениями: None")
    label_selected_photos.pack(pady=5)

    label_save_path = tk.Label(root, text="Директория со статистическими файлами: None")
    label_save_path.pack(pady=5)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)

    btn_choose_photos = tk.Button(button_frame, text="Выбрать директорию с изображениями", command=choosephotos)
    btn_choose_photos.pack(side=tk.LEFT, padx=5)

    btn_save_path = tk.Button(button_frame, text="Сохранить таблицу в", command=savePath)
    btn_save_path.pack(side=tk.LEFT, padx=5)

    btn_analyze = tk.Button(button_frame, text="Анализировать", command=analyze)
    btn_analyze.pack(side=tk.LEFT, padx=5)

    return root


if __name__ == "__main__":
    inputDirectory = ''
    outputXLSXPath = ''
    outputphotoDir = ''

    root = create_interface()
    root.mainloop()