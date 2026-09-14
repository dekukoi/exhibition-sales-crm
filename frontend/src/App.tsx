import { Route, Routes } from "react-router-dom";

import SearchPage from "@/pages/SearchPage";
import CompanyDetailPage from "@/pages/CompanyDetailPage";
import FollowUpsPage from "@/pages/FollowUpsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<SearchPage />} />
      <Route path="/companies/:id" element={<CompanyDetailPage />} />
      <Route path="/follow-ups" element={<FollowUpsPage />} />
    </Routes>
  );
}
