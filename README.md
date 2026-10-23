# Thermal Image-Based Paddy Leaf Disease Detection System

A complete full-stack machine learning application that detects and classifies 6 major paddy leaf diseases from uploaded thermal images using a fine-tuned PyTorch ResNet50 model deployed natively inside Java Spring Boot via ONNX Runtime.

---

## Technical Architecture

```
 ┌─────────────────────────────────────────────────────────┐
 │                  React + Vite Frontend                   │
 │ (Dashboard, Upload Thermal Image, History, Details)     │
 └────────────────────────────┬────────────────────────────┘
                              │ REST API (JSON / Multipart)
 ┌────────────────────────────▼────────────────────────────┐
 │               Spring Boot 3.2 Backend (Java 21)         │
 │ (Auth Controller, Prediction Controller, Stats Controller)│
 └──────────────┬───────────────────────────┬──────────────┘
                │                           │
 ┌──────────────▼──────────────┐   ┌────────▼──────────────┐
 │       MySQL 8.x/9.x DB      │   │   Java ONNX Runtime   │
 │   (User, Prediction data)   │   │ (ResNet50 ONNX Model) │
 └─────────────────────────────┘   └───────────────────────┘
```

---

## Mandatory Technology Stack

- **Frontend**: React 18, Vite, JavaScript, Lucide Icons, Vanilla CSS
- **Backend**: Java 21, Spring Boot 3.2, Spring Web, Spring Data JPA, Hibernate, MySQL Driver, Java ONNX Runtime 1.18.0
- **Machine Learning**: Python 3.14, PyTorch, `timm`, OpenCV, NumPy, ONNX Runtime
- **Database**: MySQL 9.6 (`paddy_disease_db`)

---

## Multiclass Classification (6 Paddy Leaf Conditions)

0. **Bacterial Leaf Blight (`BLB`)**
1. **Rice Blast (`Blast`)**
2. **Healthy (`healthy`)**
3. **Hispa (`hispa`)**
4. **Leaf Folder (`leaf_folder`)**
5. **Brown Leaf Spot (`leaf_spot`)**

---

## Empirical Model Performance

- **Backbone**: `ResNet50` fine-tuned with OpenCV Median Blur ($k=3$) and CLAHE ($\text{clipLimit}=2.0, \text{tileGridSize}=(8,8)$).
- **Validation Accuracy Obtained**: `56.25%` (Reported from actual empirical model training, no hardcoded paper numbers).

---

## Project Structure

```
MLProject/
├── ml/
│   ├── src/
│   │   ├── preprocess.py        # OpenCV Median Blur + CLAHE pipeline
│   │   ├── model.py             # PyTorch ResNet50 timm architecture
│   │   ├── export_onnx.py       # Single-file ONNX export tool
│   │   ├── predict.py           # CLI prediction verifier
│   │   └── evaluate.py          # Metrics calculation script
│   ├── notebooks/
│   │   └── recentOne.ipynb      # Source PyTorch training notebook
│   ├── models/
│   │   ├── best_model.pth       # Saved PyTorch model checkpoint
│   │   └── resnet50_paddy.onnx  # Exported 94MB single-file ONNX model
│   ├── results/
│   │   └── evaluation_metrics.json
│   ├── requirements.txt
│   └── README.md
│
├── backend/
│   ├── pom.xml
│   └── src/
│       └── main/
│           ├── java/com/project/paddy/
│           │   ├── PaddyDiseaseApplication.java
│           │   ├── config/ (CorsConfig.java)
│           │   ├── controller/ (AuthController, PredictionController, DashboardController)
│           │   ├── dto/ (AuthResponse, PredictionResponse, DashboardStatsResponse)
│           │   ├── entity/ (User, Prediction)
│           │   ├── exception/ (GlobalExceptionHandler)
│           │   ├── ml/ (OnnxInferenceService - Java ONNX model loader)
│           │   ├── repository/ (UserRepository, PredictionRepository)
│           │   └── service/ (AuthService, PredictionService)
│           └── resources/
│               └── application.properties
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── components/ (Navbar, Footer)
│       ├── context/ (AuthContext)
│       ├── pages/ (Home, Login, Register, Dashboard, Predict, History, ModelPerformance)
│       ├── services/ (api.js)
│       ├── App.jsx
│       └── main.jsx
│
├── README.md
└── .gitignore
```

---

## How to Run the Application

### 1. Database Setup
Ensure MySQL is running on `localhost:3306`. The database `paddy_disease_db` will be created automatically on startup.
Update `backend/src/main/resources/application.properties` credentials if necessary:
```properties
spring.datasource.username=root
spring.datasource.password=passwordMysql@52
```

### 2. Start Spring Boot Backend
```bash
cd backend
mvn clean package -DskipTests
java -jar target/paddy-disease-backend-1.0.0.jar
```
*Backend will run on `http://localhost:8080`.*

### 3. Start React + Vite Frontend
```bash
cd frontend
npm install
npm run dev
```
*Frontend will run on `http://localhost:5173`.*

---

## Key API Endpoints

- `POST /api/auth/register`: Register user
- `POST /api/auth/login`: Authenticate user
- `POST /api/predictions`: Upload thermal leaf image, perform ONNX inference, save to MySQL
- `GET /api/predictions?userId={id}`: Fetch user scan history
- `GET /api/dashboard/stats?userId={id}`: Fetch aggregated MySQL stats and disease breakdown
