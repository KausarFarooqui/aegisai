import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { LoadingState } from "@/components/States";
import { ProcessListPage } from "@/pages/ProcessList";
import { ProcessDetailPage } from "@/pages/ProcessDetail";
import { RoleListPage, RoleDetailPage } from "@/pages/Roles";
import { SkillListPage, SkillDetailPage } from "@/pages/Skills";
import { OpportunitiesPage } from "@/pages/Opportunities";
import { AnalyzePage } from "@/pages/Analyze";

// Lazy-loaded: both pull in a heavy charting/graph library (recharts,
// reactflow) that most navigations to other pages don't need to pay for
// on first load.
const DashboardPage = lazy(() =>
  import("@/pages/Dashboard").then((m) => ({ default: m.DashboardPage })),
);
const GraphPage = lazy(() => import("@/pages/Graph").then((m) => ({ default: m.GraphPage })));

function PageFallback() {
  return (
    <div className="flex h-screen items-center justify-center">
      <LoadingState label="Loading" />
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/graph" element={<GraphPage />} />
            <Route path="/processes" element={<ProcessListPage />} />
            <Route path="/processes/:id" element={<ProcessDetailPage />} />
            <Route path="/roles" element={<RoleListPage />} />
            <Route path="/roles/:id" element={<RoleDetailPage />} />
            <Route path="/skills" element={<SkillListPage />} />
            <Route path="/skills/:id" element={<SkillDetailPage />} />
            <Route path="/opportunities" element={<OpportunitiesPage />} />
            <Route path="/analyze" element={<AnalyzePage />} />
          </Routes>
        </Suspense>
      </Layout>
    </BrowserRouter>
  );
}
