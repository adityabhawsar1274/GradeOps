import { FormEvent, ReactNode, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { api, TokenResponse, UserRole } from "./api";
import InstructorDashboard from "./pages/InstructorDashboard";
import TAReview from "./pages/TAReview";

function LoginPage() {
  const nav = useNavigate();
  const [email, setEmail] = useState("instructor@gradeops.edu");
  const [password, setPassword] = useState("instructor123");
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const data: TokenResponse = await api.login(email, password);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("role", data.role);
      localStorage.setItem("full_name", data.full_name);
      nav(data.role === "ta" ? "/review" : "/instructor");
    } catch {
      setError("Invalid credentials");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <form onSubmit={onSubmit} className="w-full max-w-md bg-white shadow-lg rounded-2xl p-8 space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">GradeOps</h1>
          <p className="text-slate-500 text-sm">Human-in-the-Loop AI Exam Grading</p>
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <input
          className="w-full border rounded-lg px-3 py-2"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
        />
        <input
          className="w-full border rounded-lg px-3 py-2"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
        />
        <button className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2 font-medium">
          Sign in
        </button>
        <div className="text-xs text-slate-500 space-y-1">
          <p>Instructor: instructor@gradeops.edu / instructor123</p>
          <p>TA: ta@gradeops.edu / ta123456</p>
        </div>
      </form>
    </div>
  );
}

function RequireAuth({ children, role }: { children: ReactNode; role?: UserRole }) {
  const token = localStorage.getItem("token");
  const userRole = localStorage.getItem("role") as UserRole | null;
  if (!token) return <Navigate to="/login" replace />;
  if (role && userRole !== role) return <Navigate to={userRole === "ta" ? "/review" : "/instructor"} replace />;
  return children;
}

function Shell({ children }: { children: ReactNode }) {
  const nav = useNavigate();
  const name = localStorage.getItem("full_name");
  const role = localStorage.getItem("role");

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b px-6 py-3 flex items-center justify-between">
        <div>
          <h1 className="font-semibold text-slate-900">GradeOps</h1>
          <p className="text-xs text-slate-500">{role?.toUpperCase()} portal</p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-600">{name}</span>
          <button
            className="text-sm text-brand-600"
            onClick={() => {
              localStorage.clear();
              nav("/login");
            }}
          >
            Logout
          </button>
        </div>
      </header>
      <main className="p-6">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/instructor"
        element={
          <RequireAuth role="instructor">
            <Shell>
              <InstructorDashboard />
            </Shell>
          </RequireAuth>
        }
      />
      <Route
        path="/review"
        element={
          <RequireAuth role="ta">
            <Shell>
              <TAReview />
            </Shell>
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
