import os
import uuid
from werkzeug.utils import secure_filename
from backend_python.config import Config
from backend_python.db.database import get_db_connection
from backend_python.services.auth_service import get_user_by_id
from backend_python.services.pytorch_service import get_inference_service

DISEASE_GENERAL_INFO = {
    "Bacterial Leaf Blight": "Bacterial Leaf Blight is caused by Xanthomonas oryzae. Symptoms include leaf wilting and yellowing along leaf margins. Thermal imaging reveals elevated surface temperatures due to compromised stomatal transpiration.",
    "Rice Blast": "Rice Blast is caused by Magnaporthe oryzae. Symptoms include diamond-shaped thermal lesions. Early detection via thermal scanning prevents leaf necrosis and crop loss.",
    "Healthy": "Paddy leaf exhibits uniform thermal dissipation and healthy stomatal conductance. No physiological stress detected.",
    "Hispa": "Paddy Hispa damage creates linear scrape marks on leaves. Thermal signatures show localized heat pockets where chlorophyll and cuticle layers have been damaged.",
    "Leaf Folder": "Leaf Folder larvae roll leaves longitudinally. Thermal imaging captures temperature spikes inside folded leaf structures.",
    "Brown Leaf Spot": "Brown Leaf Spot is caused by Bipolaris oryzae. Symptoms include circular brown lesions with distinct thermal boundary variance."
}

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
MAX_BATCH_SIZE = 10

def validate_image_file(file):
    if not file or file.filename == '':
        raise ValueError("Please select and upload a valid thermal image file.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension for '{file.filename}'. Only .jpg, .jpeg, .png, .bmp, .webp are allowed.")

    if file.mimetype and not file.mimetype.startswith('image/'):
        raise ValueError(f"Uploaded file '{file.filename}' is not a supported image type (JPEG/PNG/BMP/WebP).")

def predict_single_image(file, user_id=1, conn=None):
    """
    Processes a single image, evaluates validity, and persists ONLY valid predictions to MySQL.
    """
    validate_image_file(file)

    original_filename = secure_filename(file.filename) or "thermal_image.jpg"
    file_ext = os.path.splitext(original_filename)[1] or ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_ext}"

    # Ensure upload directory exists
    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
    target_path = os.path.join(Config.UPLOAD_DIR, unique_filename)

    file.save(target_path)

    # Run PyTorch ResNet50 inference & OOD validation
    inference_service = get_inference_service()
    result = inference_service.predict(target_path)

    image_url = f"/uploads/{unique_filename}"

    # Check if image was rejected by validation layer
    if not result.get("validImage", True):
        # Do NOT save rejected predictions in MySQL
        return {
            "error": False,
            "validImage": False,
            "predictionId": None,
            "imageName": original_filename,
            "imageUrl": image_url,
            "disease": None,
            "diseaseKey": None,
            "confidence": None,
            "confidencePercentage": None,
            "status": result.get("status", "INVALID_IMAGE"),
            "message": result.get("message", "The uploaded image does not appear to be a valid thermal paddy leaf image."),
            "generalInfo": None
        }

    confidence = result["confidence"]
    confidence_pct = f"{confidence * 100:.1f}%"

    # Save ONLY valid predictions to MySQL database
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO predictions 
                (user_id, image_name, image_path, predicted_disease, disease_key, confidence, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(6))
            """, (
                user_id,
                original_filename,
                image_url,
                result["diseaseName"],
                result["diseaseKey"],
                confidence,
                result["status"]
            ))
            prediction_id = cursor.lastrowid

            cursor.execute("SELECT created_at FROM predictions WHERE id = %s", (prediction_id,))
            created_at = cursor.fetchone()["created_at"].isoformat()

        general_info = DISEASE_GENERAL_INFO.get(result["diseaseName"], "General paddy leaf thermal scan completed.")

        return {
            "error": False,
            "validImage": True,
            "predictionId": prediction_id,
            "imageName": original_filename,
            "imageUrl": image_url,
            "disease": result["diseaseName"],
            "diseaseKey": result["diseaseKey"],
            "confidence": confidence,
            "confidencePercentage": confidence_pct,
            "status": result["status"],
            "timestamp": created_at,
            "generalInfo": general_info
        }
    finally:
        if should_close:
            conn.close()

def predict_and_save_batch(files, user_id=1):
    """
    Processes multiple thermal image uploads independently.
    Creates MySQL prediction records ONLY for valid thermal images.
    Reports batch summary: totalUploaded, validPredictions, rejectedImages.
    """
    if not files or len(files) == 0:
        raise ValueError("Please select at least one thermal image file.")

    if len(files) > MAX_BATCH_SIZE:
        raise ValueError(f"Maximum batch size exceeded. You can upload up to {MAX_BATCH_SIZE} images at a time.")

    # Verify user exists
    get_user_by_id(user_id)

    conn = get_db_connection()
    results = []
    valid_predictions_count = 0
    rejected_images_count = 0
    healthy_count = 0
    diseased_count = 0
    disease_dist = {}

    try:
        for file in files:
            try:
                res = predict_single_image(file, user_id, conn=conn)
                results.append(res)

                if res.get("validImage"):
                    valid_predictions_count += 1
                    disease = res["disease"]
                    if disease == "Healthy":
                        healthy_count += 1
                    else:
                        diseased_count += 1

                    disease_dist[disease] = disease_dist.get(disease, 0) + 1
                else:
                    rejected_images_count += 1

            except Exception as file_err:
                filename = getattr(file, 'filename', 'thermal_image.jpg')
                rejected_images_count += 1
                results.append({
                    "error": True,
                    "validImage": False,
                    "imageName": filename,
                    "status": "INVALID_FILE",
                    "message": str(file_err)
                })

        return {
            "totalUploaded": len(files),
            "totalImages": len(files),
            "validPredictions": valid_predictions_count,
            "rejectedImages": rejected_images_count,
            "healthyCount": healthy_count,
            "diseasedCount": diseased_count,
            "diseaseDistribution": disease_dist,
            "results": results
        }
    finally:
        conn.close()

def predict_and_save(file, user_id=1):
    """
    Backward-compatible single file prediction method.
    """
    return predict_single_image(file, user_id)

def get_user_predictions(user_id=1):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, image_name, image_path, predicted_disease, disease_key, confidence, status, created_at
                FROM predictions
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()

            res = []
            for r in rows:
                confidence = r['confidence']
                res.append({
                    "predictionId": r['id'],
                    "imageName": r['image_name'],
                    "imageUrl": r['image_path'],
                    "disease": r['predicted_disease'],
                    "diseaseKey": r['disease_key'],
                    "confidence": confidence,
                    "confidencePercentage": f"{confidence * 100:.1f}%",
                    "status": r['status'],
                    "timestamp": r['created_at'].isoformat(),
                    "generalInfo": DISEASE_GENERAL_INFO.get(r['predicted_disease'], "General informational report.")
                })
            return res
    finally:
        conn.close()

def get_prediction_by_id(prediction_id, user_id=1):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, image_name, image_path, predicted_disease, disease_key, confidence, status, created_at
                FROM predictions
                WHERE id = %s
            """, (prediction_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Prediction not found with ID: {prediction_id}")

            if row['user_id'] != int(user_id):
                raise ValueError("Unauthorized access to prediction record.")

            confidence = row['confidence']
            return {
                "predictionId": row['id'],
                "imageName": row['image_name'],
                "imageUrl": row['image_path'],
                "disease": row['predicted_disease'],
                "diseaseKey": row['disease_key'],
                "confidence": confidence,
                "confidencePercentage": f"{confidence * 100:.1f}%",
                "status": row['status'],
                "timestamp": row['created_at'].isoformat(),
                "generalInfo": DISEASE_GENERAL_INFO.get(row['predicted_disease'], "General informational report.")
            }
    finally:
        conn.close()

def get_dashboard_stats(user_id=1):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as cnt FROM predictions WHERE user_id = %s", (user_id,))
            total = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) as cnt FROM predictions WHERE user_id = %s AND predicted_disease = 'Healthy'", (user_id,))
            healthy = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) as cnt FROM predictions WHERE user_id = %s AND predicted_disease != 'Healthy'", (user_id,))
            diseased = cursor.fetchone()['cnt']

            cursor.execute("""
                SELECT predicted_disease, COUNT(*) as cnt 
                FROM predictions 
                WHERE user_id = %s 
                GROUP BY predicted_disease
            """, (user_id,))
            dist_rows = cursor.fetchall()

            dist_map = {}
            for r in dist_rows:
                dist_map[r['predicted_disease']] = r['cnt']

            cursor.execute("""
                SELECT id, image_name, image_path, predicted_disease, disease_key, confidence, status, created_at
                FROM predictions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 5
            """, (user_id,))
            top5 = cursor.fetchall()

            recent = []
            for r in top5:
                confidence = r['confidence']
                recent.append({
                    "predictionId": r['id'],
                    "imageName": r['image_name'],
                    "imageUrl": r['image_path'],
                    "disease": r['predicted_disease'],
                    "diseaseKey": r['disease_key'],
                    "confidence": confidence,
                    "confidencePercentage": f"{confidence * 100:.1f}%",
                    "status": r['status'],
                    "timestamp": r['created_at'].isoformat(),
                    "generalInfo": None
                })

            return {
                "totalPredictions": total,
                "healthyPredictions": healthy,
                "diseasedPredictions": diseased,
                "diseaseDistribution": dist_map,
                "recentPredictions": recent
            }
    finally:
        conn.close()

def clear_user_predictions(user_id=1):
    """
    Deletes all prediction records for the specified user from MySQL.
    Safely cleans up associated uploaded image files if no longer referenced.
    Resets AUTO_INCREMENT if the predictions table becomes empty.
    """
    get_user_by_id(user_id)

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Fetch image paths belonging to user's predictions
            cursor.execute("SELECT image_path FROM predictions WHERE user_id = %s", (user_id,))
            user_image_paths = [r['image_path'] for r in cursor.fetchall()]

            # 2. Delete predictions belonging ONLY to this user
            cursor.execute("DELETE FROM predictions WHERE user_id = %s", (user_id,))
            deleted_count = cursor.rowcount

            # 3. Clean up physical image files if no other prediction uses them
            deleted_files_count = 0
            for img_path in user_image_paths:
                if not img_path or not img_path.startswith('/uploads/'):
                    continue

                cursor.execute("SELECT COUNT(*) as cnt FROM predictions WHERE image_path = %s", (img_path,))
                ref_count = cursor.fetchone()['cnt']

                if ref_count == 0:
                    filename = os.path.basename(img_path)
                    physical_file = os.path.join(Config.UPLOAD_DIR, filename)
                    if os.path.exists(physical_file):
                        try:
                            os.remove(physical_file)
                            deleted_files_count += 1
                        except Exception as fe:
                            pass

            # 4. Reset AUTO_INCREMENT if predictions table is completely empty
            cursor.execute("SELECT COUNT(*) as cnt FROM predictions")
            total_remaining = cursor.fetchone()['cnt']
            if total_remaining == 0:
                cursor.execute("ALTER TABLE predictions AUTO_INCREMENT = 1")

            return {
                "message": "Prediction history cleared successfully",
                "deletedCount": deleted_count,
                "deletedFilesCount": deleted_files_count
            }
    finally:
        conn.close()
