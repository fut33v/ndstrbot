import base64
img_data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
with open('/app/test_image.png', 'wb') as f:
    f.write(base64.b64decode(img_data))
