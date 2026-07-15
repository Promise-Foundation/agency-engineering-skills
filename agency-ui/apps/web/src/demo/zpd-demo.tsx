/**
 * A LIVE, writable demo plugin -- the stand-in for a skill (ZPD) that fetches
 * from a mutable store. It exists to make the mutation seam visible in the
 * running shell, right beside the read-only LTP and Hypothesize plugins:
 *
 *   - registers a `createMemorySource` (determinism: "live", writable, watchable);
 *   - its resources render with the shell's "editable · live" badge (canWrite === true);
 *   - creating/updating a learning job goes through `host.resources.apply(...)`,
 *     the exact same path a real backend-backed source would implement.
 *
 * Nothing in the shell changed to host it. That is the whole point.
 */

import { useEffect, useState } from "react";
import type {
  AgencyHost,
  AgencyResource,
  AgencySkillPlugin,
  HostProps,
  ResourceComponentProps,
} from "@agency/skill-sdk";
import { createMemorySource } from "@agency/core";
import { Card, Chip, Field, Toolbar } from "@agency/ui-kit";
import "./zpd-demo.css";

const SKILL_ID = "zpd";
const TYPE = "zpd.learning-job";

interface LearningJob {
  question: string;
  blocked: boolean;
  estimate: number;
  [key: string]: unknown;
}

const SEED: AgencyResource<LearningJob>[] = [
  {
    id: "job-1",
    type: TYPE,
    ownerSkill: SKILL_ID,
    schemaVersion: 1,
    title: "Establish identity by matching names",
    status: "blocked",
    data: { question: "Does matching names establish identity?", blocked: true, estimate: 0.35 },
    provenance: { determinism: "live", sourceId: "zpd:store" },
  },
  {
    id: "job-2",
    type: TYPE,
    ownerSkill: SKILL_ID,
    schemaVersion: 1,
    title: "Read a causal claim's scope",
    status: "active",
    data: { question: "Can the learner state a claim's population?", blocked: false, estimate: 0.6 },
    provenance: { determinism: "live", sourceId: "zpd:store" },
  },
];

function useLiveJobs(host: AgencyHost): AgencyResource<LearningJob>[] {
  const [jobs, setJobs] = useState<AgencyResource<LearningJob>[]>([]);
  useEffect(() => {
    let active = true;
    const reload = () =>
      void host.resources.list({ type: TYPE }).then((list) => {
        if (active) setJobs(list as AgencyResource<LearningJob>[]);
      });
    reload();
    const stop = host.resources.watch({ type: TYPE }, reload); // live updates on apply()
    return () => {
      active = false;
      stop();
    };
  }, [host]);
  return jobs;
}

function ZpdPage({ host }: HostProps) {
  const jobs = useLiveJobs(host);
  const [question, setQuestion] = useState("");
  const writable = host.resources.canWrite(TYPE);

  async function addJob() {
    if (!question.trim()) return;
    const id = `job-${jobs.length + 1}-${question.length}`;
    await host.resources.apply({
      kind: "created",
      ref: { type: TYPE, id },
      data: { question: question.trim(), blocked: true, estimate: 0.3 } satisfies LearningJob,
    });
    host.notifications.info(`Created ${id} in the live store`);
    setQuestion("");
  }

  return (
    <div className="zpd-page">
      <header>
        <h1>Learning jobs</h1>
        <Chip tone={writable ? "positive" : "neutral"}>{writable ? "live · writable" : "read-only"}</Chip>
      </header>
      <p className="muted">
        A live source (the ZPD-store stand-in). Creating a job writes through the very same
        federated <code>apply()</code> a real backend would implement.
      </p>
      {writable && (
        <Toolbar>
          <input
            className="zpd-input"
            placeholder="New learning question…"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && void addJob()}
          />
          <button className="zpd-btn" onClick={() => void addJob()}>
            Add job
          </button>
        </Toolbar>
      )}
      <div className="zpd-grid">
        {jobs.map((job) => (
          <button key={job.id} className="zpd-job" onClick={() => host.selection.select({ type: TYPE, id: job.id })}>
            <span className="zpd-job__q">{job.data.question}</span>
            <Chip tone={job.data.blocked ? "negative" : "positive"}>
              {job.data.blocked ? "blocked" : "active"}
            </Chip>
          </button>
        ))}
      </div>
    </div>
  );
}

function ZpdCard({ host }: HostProps) {
  const jobs = useLiveJobs(host);
  const blocked = jobs.filter((job) => job.data.blocked).length;
  return (
    <Card
      title="Learning jobs"
      subtitle="live · writable"
      actions={
        <button className="zpd-link" onClick={() => host.navigation.navigate("/zpd")}>
          Open ›
        </button>
      }
    >
      <Toolbar>
        <Chip tone="info">{jobs.length} jobs</Chip>
        <Chip tone="negative">{blocked} blocked</Chip>
      </Toolbar>
    </Card>
  );
}

function ZpdJobView({ host, resource }: ResourceComponentProps) {
  const job = resource.data as LearningJob;
  const writable = host.resources.canWrite(TYPE);
  return (
    <div className="zpd-detail">
      <p className="zpd-detail__q">{job.question}</p>
      <Field label="Blocked">{job.blocked ? "yes" : "no"}</Field>
      <Field label="Capability estimate">{Math.round((job.estimate ?? 0) * 100)}%</Field>
      {writable && job.blocked && (
        <button
          className="zpd-btn"
          onClick={() =>
            void host.resources
              .apply({ kind: "updated", ref: { type: TYPE, id: resource.id }, data: { ...job, blocked: false } })
              .then(() => host.notifications.info(`${resource.id} unblocked`))
          }
        >
          Mark unblocked
        </button>
      )}
    </div>
  );
}

export const zpdDemoPlugin: AgencySkillPlugin = {
  manifest: {
    id: SKILL_ID,
    name: "ZPD (demo)",
    version: "0.1.0",
    description: "A live, writable skill demonstrating that mutable data hosts cleanly on the same shell.",
    contributions: {
      navigation: [{ id: "zpd.nav", label: "ZPD (demo)", to: "/zpd", order: 30 }],
      routes: [{ id: "zpd.route", path: "/zpd", title: "ZPD", component: ZpdPage }],
      dashboardCards: [{ id: "zpd.card", title: "Learning jobs", component: ZpdCard, order: 30 }],
      resourceTypes: [{ type: TYPE, label: "Learning job" }],
      resourceViews: [{ id: "zpd.view", resourceTypes: [TYPE], component: ZpdJobView }],
      commands: [{ id: "zpd.seed", title: "ZPD: add a sample learning job" }],
    },
  },
  activate(context) {
    const unregisterSource = context.resources.registerSource(
      createMemorySource({ id: "zpd:store", ownerSkill: SKILL_ID, types: [TYPE], seedResources: SEED }),
    );
    const unregisterCommand = context.commands.register("zpd.seed", async () => {
      const id = `job-sample-${Date.now()}`;
      await context.resources.apply({
        kind: "created",
        ref: { type: TYPE, id },
        data: { question: "A newly seeded question", blocked: true, estimate: 0.25 },
      });
      return { summary: `created ${id}`, createdResources: [`${TYPE}:${id}`] };
    });
    return {
      deactivate() {
        unregisterCommand();
        unregisterSource();
      },
    };
  },
};
