import { initializeApp, getApps } from "firebase/app";
import { getFirestore } from "firebase/firestore";
import { getStorage } from "firebase/storage";

const firebaseConfig = {
  apiKey: "AIzaSyD5oI5e2m5t7LLKQ_t5ZbUZTxVduX0h1D8",
  authDomain: "enha-server.firebaseapp.com",
  projectId: "enha-server",
  storageBucket: "enha-server.firebasestorage.app",
  messagingSenderId: "770987674067",
  appId: "1:770987674067:web:a4895cdd6a9b0233adc726",
  measurementId: "G-0MPMNT9DZ7"
};

export const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const storage = getStorage(app);
