const API = "/api";

export type UserRole = "instructor" | "ta";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  full_name: string;
}

export interface Exam {
  id: number;
  title: string;
  description: string;
  status: string;
  submission_count: number;
}

export interface Grade {
  id: number;
  ai_score: number;
  ai_max_score: number;
  ai_justification: string;
  final_score: number | null;
  status: "pending" | "approved" | "overridden";
}

export interface ReviewItem {
  grade_id: number;
  exam_id: number;
  exam_title: string;
  student_id: string;
  question_id: string;
  page_number: number;
  image_url: string | null;
  transcription: string;
  grade: Grade;
  plagiarism_flags: { id: number; similar_answer_id: number; similarity_score: number; reason: string }[];
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      ...authHeaders(),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  return res.json();
}

export const api = {
  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) throw new Error("Login failed");
    return res.json() as Promise<TokenResponse>;
  },
  listExams: () => request<Exam[]>("/exams"),
  createExam: (title: string, description: string) =>
    request<Exam>("/exams", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description }),
    }),
  seedDemo: () => request<{ exam_id: number }>("/exams/demo", { method: "POST" }),
  uploadRubric: async (examId: number, file: File) => {
    const fd = new FormData();
    fd.append("rubric", file);
    const res = await fetch(`${API}/exams/${examId}/rubric`, {
      method: "POST",
      headers: authHeaders(),
      body: fd,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  uploadSubmissions: async (examId: number, files: FileList, studentIds: string) => {
    const fd = new FormData();
    Array.from(files).forEach((f) => fd.append("files", f));
    fd.append("student_ids", studentIds);
    const res = await fetch(`${API}/exams/${examId}/submissions`, {
      method: "POST",
      headers: authHeaders(),
      body: fd,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  processSync: (examId: number) =>
    request<{ answers_graded: number; plagiarism_flags: number }>(`/exams/${examId}/process-sync`, {
      method: "POST",
    }),
  reviewQueue: (status = "pending") => request<ReviewItem[]>(`/review/queue?status=${status}`),
  reviewStats: () =>
    request<{ pending: number; approved: number; overridden: number; plagiarism_flags: number }>("/review/stats"),
  reviewAction: (gradeId: number, action: "approve" | "override", finalScore?: number, reason?: string) =>
    request(`/review/${gradeId}/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, final_score: finalScore, override_reason: reason }),
    }),
};
