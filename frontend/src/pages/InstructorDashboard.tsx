import { useEffect, useState } from "react";
import { api, Exam } from "../api";

export default function InstructorDashboard() {
  const [exams, setExams] = useState<Exam[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selectedExam, setSelectedExam] = useState<number | null>(null);
  const [studentIds, setStudentIds] = useState("");
  const [message, setMessage] = useState("");

  async function refresh() {
    setExams(await api.listExams());
  }

  useEffect(() => {
    refresh();
  }, []);

  async function createExam() {
    if (!title.trim()) return;
    const exam = await api.createExam(title, description);
    setTitle("");
    setDescription("");
    setSelectedExam(exam.id);
    setMessage(`Created exam #${exam.id}`);
    refresh();
  }

  async function seedDemo() {
    const res = await api.seedDemo();
    setMessage(`Demo exam ready (#${res.exam_id}) with graded submissions`);
    refresh();
  }

  async function onRubric(e: React.ChangeEvent<HTMLInputElement>) {
    if (!selectedExam || !e.target.files?.[0]) return;
    await api.uploadRubric(selectedExam, e.target.files[0]);
    setMessage("Rubric uploaded");
  }

  async function onSubmissions(e: React.ChangeEvent<HTMLInputElement>) {
    if (!selectedExam || !e.target.files?.length) return;
    await api.uploadSubmissions(selectedExam, e.target.files, studentIds);
    setMessage(`Uploaded ${e.target.files.length} submission(s)`);
    refresh();
  }

  async function processExam() {
    if (!selectedExam) return;
    const res = await api.processSync(selectedExam);
    setMessage(`Processed ${res.answers_graded} answers, ${res.plagiarism_flags} plagiarism flags`);
    refresh();
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <section className="bg-white rounded-xl shadow p-6 space-y-4">
        <h2 className="text-lg font-semibold">Create Exam</h2>
        <div className="grid md:grid-cols-2 gap-3">
          <input className="border rounded-lg px-3 py-2" placeholder="Exam title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <input className="border rounded-lg px-3 py-2" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div className="flex gap-3">
          <button onClick={createExam} className="bg-brand-600 text-white px-4 py-2 rounded-lg">Create</button>
          <button onClick={seedDemo} className="border border-brand-600 text-brand-700 px-4 py-2 rounded-lg">Load Demo Exam</button>
        </div>
        {message && <p className="text-sm text-green-700">{message}</p>}
      </section>

      <section className="bg-white rounded-xl shadow p-6 space-y-4">
        <h2 className="text-lg font-semibold">Upload & Process</h2>
        <select className="border rounded-lg px-3 py-2 w-full" value={selectedExam ?? ""} onChange={(e) => setSelectedExam(Number(e.target.value))}>
          <option value="">Select exam</option>
          {exams.map((e) => (
            <option key={e.id} value={e.id}>
              #{e.id} — {e.title} ({e.status}, {e.submission_count} submissions)
            </option>
          ))}
        </select>
        <div className="grid md:grid-cols-2 gap-4">
          <label className="block border rounded-lg p-4 cursor-pointer hover:bg-slate-50">
            <span className="font-medium">Upload Rubric JSON</span>
            <input type="file" accept="application/json" className="mt-2 block w-full" onChange={onRubric} />
          </label>
          <label className="block border rounded-lg p-4 cursor-pointer hover:bg-slate-50">
            <span className="font-medium">Upload Exam PDFs</span>
            <input type="file" multiple accept=".pdf,.txt" className="mt-2 block w-full" onChange={onSubmissions} />
          </label>
        </div>
        <input className="border rounded-lg px-3 py-2 w-full" placeholder="Student IDs comma-separated (optional)" value={studentIds} onChange={(e) => setStudentIds(e.target.value)} />
        <button onClick={processExam} disabled={!selectedExam} className="bg-emerald-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg">
          Run OCR + AI Grading Pipeline
        </button>
      </section>

      <section className="bg-white rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold mb-3">Exams</h2>
        <div className="divide-y">
          {exams.map((e) => (
            <div key={e.id} className="py-3 flex justify-between">
              <div>
                <p className="font-medium">{e.title}</p>
                <p className="text-sm text-slate-500">{e.description}</p>
              </div>
              <div className="text-right text-sm">
                <p className="uppercase tracking-wide text-slate-500">{e.status}</p>
                <p>{e.submission_count} submissions</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
