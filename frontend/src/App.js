import "@/App.css";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, ProtectedRoute } from "@/lib/auth";
import NavBar from "@/components/NavBar";
import AuthCallback from "@/components/AuthCallback";
import Landing from "@/pages/Landing";
import JobsCity from "@/pages/JobsCity";
import ApplicantsCity from "@/pages/ApplicantsCity";
import JobDetail from "@/pages/JobDetail";
import ApplicantDetail from "@/pages/ApplicantDetail";
import Profile from "@/pages/Profile";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Onboarding from "@/pages/Onboarding";
import Compare from "@/pages/Compare";
import { Toaster } from "sonner";

function ShellRoutes() {
  const location = useLocation();
  // Hard-route Google callback: detect session_id in URL fragment synchronously
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }
  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/jobs-city" element={<JobsCity />} />
        <Route path="/applicants-city" element={<ApplicantsCity />} />
        <Route path="/jobs/:id" element={<JobDetail />} />
        <Route path="/applicants/:id" element={<ApplicantDetail />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <Onboarding />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Landing />} />
      </Routes>
    </>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <ShellRoutes />
          <Toaster theme="dark" position="top-right" />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
