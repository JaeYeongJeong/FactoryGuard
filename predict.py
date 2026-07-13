from ultralytics import YOLO

# 학습한 모델 불러오기
model = YOLO("runs/detect/train-2/weights/best.pt")

results = model.predict(
    source="./data/helmet1.jpeg",
    conf=0.5,
    save=True,
    show=False,
    device=0
)

result = results[0]

for box in result.boxes:
    cls = int(box.cls)
    conf = float(box.conf)

    print(
        result.names[cls],
        conf,
        box.xyxy[0].tolist()
    )