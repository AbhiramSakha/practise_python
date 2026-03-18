import os

# Define the project structure and file contents
project_name = "banking_dashboard_pro"

files = {
    # ---------------------------------------------------------
    # 1. DOCKER & CONFIGURATION (Making it "Real")
    # ---------------------------------------------------------
    "docker-compose.yml": """version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=banking_db
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://postgres:password@db/banking_db

  frontend:
    build: ./frontend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000

volumes:
  postgres_data:
""",

    # ---------------------------------------------------------
    # 2. BACKEND (FastAPI + PostgreSQL)
    # ---------------------------------------------------------
    "backend/Dockerfile": """FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
""",
    
    "backend/requirements.txt": """fastapi
uvicorn
sqlalchemy
psycopg2-binary
pydantic
passlib[bcrypt]
python-jose[cryptography]
python-multipart
""",

    "backend/app/__init__.py": "",

    "backend/app/database.py": """from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/banking_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",

    "backend/app/models.py": """from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, TIMESTAMP, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    accounts = relationship("Account", back_populates="owner")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bank_name = Column(String)
    account_type = Column(String)
    balance = Column(Numeric(10, 2))
    masked_number = Column(String)
    owner = relationship("User", back_populates="accounts")
""",

    "backend/app/main.py": """from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, database
from pydantic import BaseModel
from typing import List
import random

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---
class AccountOut(BaseModel):
    id: int
    bank_name: str
    account_type: str
    balance: float
    masked_number: str
    class Config:
        orm_mode = True

# --- Routes ---
@app.get("/")
def read_root():
    return {"status": "Banking System Online"}

@app.get("/accounts", response_model=List[AccountOut])
def get_accounts(db: Session = Depends(database.get_db)):
    # Simulating Real-Time Data: 
    # In a real app, this comes from the DB. 
    # For this demo, we verify DB connection but return mocked 'live' data if empty.
    accounts = db.query(models.Account).all()
    
    if not accounts:
        return [
            {"id": 1, "bank_name": "Chase", "account_type": "Checking", "balance": random.uniform(5000, 5500), "masked_number": "**** 4829"},
            {"id": 2, "bank_name": "Citi", "account_type": "Savings", "balance": random.uniform(12000, 12100), "masked_number": "**** 9921"},
        ]
    return accounts
""",

    # ---------------------------------------------------------
    # 3. FRONTEND (React + Tailwind + Real-Time Polling)
    # ---------------------------------------------------------
    "frontend/Dockerfile": """FROM node:18
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
CMD ["npm", "run", "dev", "--", "--host"]
""",

    "frontend/package.json": """{
  "name": "banking-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.6.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.5",
    "vite": "^5.0.0"
  }
}
""",

    "frontend/vite.config.js": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  }
})
""",

    "frontend/tailwind.config.js": """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
""",

    "frontend/postcss.config.js": """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
""",

    "frontend/index.html": """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NeoBank Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""",

    "frontend/src/index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
    background-color: #f3f4f6;
}
""",

    "frontend/src/main.jsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",

    "frontend/src/api/axios.js": """import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"
});

export default api;
""",

    "frontend/src/App.jsx": """import Dashboard from './pages/Dashboard';

function App() {
  return (
    <Dashboard />
  );
}

export default App;
""",

    "frontend/src/pages/Dashboard.jsx": """import { useState, useEffect } from 'react';
import api from '../api/axios';

export default function Dashboard() {
  const [accounts, setAccounts] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // REAL-TIME POLLING: Fetches new data every 3 seconds
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get('/accounts');
        setAccounts(response.data);
        setLastUpdated(new Date());
      } catch (error) {
        console.error("Connection error:", error);
      }
    };

    fetchData(); // Initial fetch
    const interval = setInterval(fetchData, 3000); // Poll every 3s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen bg-gray-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r shadow-sm hidden md:block">
        <div className="p-6">
           <h1 className="text-2xl font-bold text-indigo-600">NeoBank</h1>
        </div>
        <nav className="mt-6">
          {['Dashboard', 'Transactions', 'Cards', 'Settings'].map(item => (
            <div key={item} className={`px-6 py-3 cursor-pointer ${item === 'Dashboard' ? 'bg-indigo-50 text-indigo-700 border-r-4 border-indigo-700' : 'text-gray-600 hover:bg-gray-50'}`}>
              {item}
            </div>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-y-auto">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-3xl font-bold text-gray-800">Dashboard</h2>
            <p className="text-sm text-gray-500 mt-1">
               Live Updates Active • Last synced: {lastUpdated.toLocaleTimeString()}
            </p>
          </div>
          <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-700 font-bold">
            JD
          </div>
        </header>

        {/* Account Cards */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {accounts.map((acc, index) => (
            <div key={index} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                   <p className="text-gray-500 text-sm font-medium">{acc.bank_name}</p>
                   <p className="text-xs text-gray-400">{acc.account_type}</p>
                </div>
                <div className="p-2 bg-indigo-50 rounded-lg">
                   <span className="text-indigo-600 text-xl">🏦</span>
                </div>
              </div>
              <h3 className="text-3xl font-bold text-gray-900 mb-2">
                ${acc.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </h3>
              <p className="text-gray-400 font-mono text-sm tracking-wider">{acc.masked_number}</p>
            </div>
          ))}
        </section>

        {/* Empty State for Transactions */}
        <section className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200 text-center">
           <div className="max-w-md mx-auto">
             <h3 className="text-lg font-semibold text-gray-800">No Recent Transactions</h3>
             <p className="text-gray-500 mt-2">Your latest transaction activity will appear here in real-time once you start spending.</p>
           </div>
        </section>
      </main>
    </div>
  );
}
"""
}

def create_project():
    # Create Root Directory
    if not os.path.exists(project_name):
        os.makedirs(project_name)
    
    print(f"🚀 Initializing '{project_name}'...")

    for path, content in files.items():
        # Construct full path
        full_path = os.path.join(project_name, path)
        directory = os.path.dirname(full_path)
        
        # Create directories if they don't exist
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Write file content
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"   Created: {path}")

    print("\n✅ PROJECT CREATED SUCCESSFULLY!")
    print("\nNext Steps:")
    print(f"1. cd {project_name}")
    print("2. docker-compose up --build")
    print("3. Open http://localhost:5173 to see your Real-Time Dashboard")

if __name__ == "__main__":
    create_project()