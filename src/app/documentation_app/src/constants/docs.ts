export interface DocEntry {
  title: string;
  navTitle?: string;
  path: string;
  sectionId: DocSectionId;
  url: string;
  githubUrl: string;
}

export interface DocSection {
  id: DocSectionId;
  title: string;
  docIds: DocId[];
}

const GITHUB_OWNER = 'cerai-iitm';
const GITHUB_REPO = 'AIEvaluationTool';
const GITHUB_BRANCH = 'dev';
const GITHUB_DOCS_PATH = 'docs';

export type DocSectionId =
  | 'overview'
  | 'docker-setup'
  | 'ai-evaluation-tool-cli'
  | 'tdms'
  | 'ai-evaluation-tool-ui'
  | 'pqet';

function buildRawRepositoryUrl(repoPath: string) {
  return `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/${GITHUB_BRANCH}/${repoPath}`;
}

function buildGithubRepositoryUrl(repoPath: string) {
  return `https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/${repoPath}`;
}

function buildRawDocUrl(path: string) {
  return buildRawRepositoryUrl(`${GITHUB_DOCS_PATH}/${path}`);
}

function buildGithubDocUrl(path: string) {
  return buildGithubRepositoryUrl(`${GITHUB_DOCS_PATH}/${path}`);
}

const docsConfig = {
  'overview-home': {
    title: 'Overview',
    navTitle: 'Introduction',
    path: 'overview/index.md',
    sectionId: 'overview',
    url: buildRawDocUrl('overview/index.md'),
    githubUrl: buildGithubDocUrl('overview/index.md'),
  },
  'overview-ai-evaluation-tool': {
    title: 'AI Evaluation Tool',
    path: 'overview/aievaluation_tool.md',
    sectionId: 'overview',
    url: buildRawDocUrl('overview/aievaluation_tool.md'),
    githubUrl: buildGithubDocUrl('overview/aievaluation_tool.md'),
  },
  'overview-docker-run': {
    title: 'Docker Run',
    path: 'overview/docker_run.md',
    sectionId: 'overview',
    url: buildRawDocUrl('overview/docker_run.md'),
    githubUrl: buildGithubDocUrl('overview/docker_run.md'),
  },
  'overview-tdms': {
    title: 'TDMS',
    path: 'overview/tdms.md',
    sectionId: 'overview',
    url: buildRawDocUrl('overview/tdms.md'),
    githubUrl: buildGithubDocUrl('overview/tdms.md'),
  },
  'overview-pqet': {
    title: 'PQET',
    path: 'overview/pqet.md',
    sectionId: 'overview',
    url: buildRawDocUrl('overview/pqet.md'),
    githubUrl: buildGithubDocUrl('overview/pqet.md'),
  },
  'docker-setup-home': {
    title: 'Docker Setup',
    navTitle: 'Overview',
    path: 'docker_setup/index.md',
    sectionId: 'docker-setup',
    url: buildRawDocUrl('docker_setup/index.md'),
    githubUrl: buildGithubDocUrl('docker_setup/index.md'),
  },
  'docker-setup-config': {
    title: 'Setup And Configuration',
    navTitle: 'Setup',
    path: 'docker_setup/setup_and_configuration.md',
    sectionId: 'docker-setup',
    url: buildRawDocUrl('docker_setup/setup_and_configuration.md'),
    githubUrl: buildGithubDocUrl('docker_setup/setup_and_configuration.md'),
  },
  'docker-setup-gpu': {
    title: 'GPU Setup',
    path: 'docker_setup/gpu_setup.md',
    sectionId: 'docker-setup',
    url: buildRawDocUrl('docker_setup/gpu_setup.md'),
    githubUrl: buildGithubDocUrl('docker_setup/gpu_setup.md'),
  },
  'docker-setup-run': {
    title: 'Docker Run',
    path: 'docker_setup/docker_run.md',
    sectionId: 'docker-setup',
    url: buildRawDocUrl('docker_setup/docker_run.md'),
    githubUrl: buildGithubDocUrl('docker_setup/docker_run.md'),
  },
  'cli-home': {
    title: 'AI Evaluation Tool CLI',
    navTitle: 'Overview',
    path: 'ai_evaluation_tool_cli/index.md',
    sectionId: 'ai-evaluation-tool-cli',
    url: buildRawDocUrl('ai_evaluation_tool_cli/index.md'),
    githubUrl: buildGithubDocUrl('ai_evaluation_tool_cli/index.md'),
  },
  'cli-initial-setup': {
    title: 'Initial Setup And Configuration',
    navTitle: 'Initial Setup',
    path: 'ai_evaluation_tool_cli/initial_setup_and_configuration.md',
    sectionId: 'ai-evaluation-tool-cli',
    url: buildRawDocUrl('ai_evaluation_tool_cli/initial_setup_and_configuration.md'),
    githubUrl: buildGithubDocUrl('ai_evaluation_tool_cli/initial_setup_and_configuration.md'),
  },
  'cli-gpu-setup': {
    title: 'GPU Setup',
    path: 'ai_evaluation_tool_cli/gpu_setup.md',
    sectionId: 'ai-evaluation-tool-cli',
    url: buildRawDocUrl('ai_evaluation_tool_cli/gpu_setup.md'),
    githubUrl: buildGithubDocUrl('ai_evaluation_tool_cli/gpu_setup.md'),
  },
  'cli-importer-execution': {
    title: 'Importer And Testcase Execution',
    navTitle: 'Importer And Execution',
    path: 'ai_evaluation_tool_cli/importer_and_testcase_execution.md',
    sectionId: 'ai-evaluation-tool-cli',
    url: buildRawDocUrl('ai_evaluation_tool_cli/importer_and_testcase_execution.md'),
    githubUrl: buildGithubDocUrl('ai_evaluation_tool_cli/importer_and_testcase_execution.md'),
  },
  'cli-analysis-report': {
    title: 'Analysis And Report',
    path: 'ai_evaluation_tool_cli/analysis_and_report.md',
    sectionId: 'ai-evaluation-tool-cli',
    url: buildRawDocUrl('ai_evaluation_tool_cli/analysis_and_report.md'),
    githubUrl: buildGithubDocUrl('ai_evaluation_tool_cli/analysis_and_report.md'),
  },
  'tdms-home': {
    title: 'TDMS',
    navTitle: 'Overview',
    path: 'tdms/index.md',
    sectionId: 'tdms',
    url: buildRawDocUrl('tdms/index.md'),
    githubUrl: buildGithubDocUrl('tdms/index.md'),
  },
  'tdms-setup': {
    title: 'TDMS Setup',
    navTitle: 'Setup',
    path: 'tdms/setup.md',
    sectionId: 'tdms',
    url: buildRawDocUrl('tdms/setup.md'),
    githubUrl: buildGithubDocUrl('tdms/setup.md'),
  },
  'tdms-access': {
    title: 'Access And Roles',
    path: 'tdms/access_and_roles.md',
    sectionId: 'tdms',
    url: buildRawDocUrl('tdms/access_and_roles.md'),
    githubUrl: buildGithubDocUrl('tdms/access_and_roles.md'),
  },
  'ui-home': {
    title: 'AI Evaluation Tool UI',
    navTitle: 'Overview',
    path: 'ai_evaluation_tool_ui/index.md',
    sectionId: 'ai-evaluation-tool-ui',
    url: buildRawDocUrl('ai_evaluation_tool_ui/index.md'),
    githubUrl: buildGithubDocUrl('ai_evaluation_tool_ui/index.md'),
  },
  'ui-setup': {
    title: 'UI Setup',
    navTitle: 'Setup',
    path: 'ai_evaluation_tool_ui/setup.md',
    sectionId: 'ai-evaluation-tool-ui',
    url: buildRawDocUrl('ai_evaluation_tool_ui/setup.md'),
    githubUrl: buildGithubDocUrl('ai_evaluation_tool_ui/setup.md'),
  },
  'ui-dashboard': {
    title: 'Using The Dashboard',
    navTitle: 'Dashboard Usage',
    path: 'ai_evaluation_tool_ui/using_the_dashboard.md',
    sectionId: 'ai-evaluation-tool-ui',
    url: buildRawDocUrl('ai_evaluation_tool_ui/using_the_dashboard.md'),
    githubUrl: buildGithubDocUrl('ai_evaluation_tool_ui/using_the_dashboard.md'),
  },
  'pqet-home': {
    title: 'PQET',
    navTitle: 'Overview',
    path: 'pqet/index.md',
    sectionId: 'pqet',
    url: buildRawDocUrl('pqet/index.md'),
    githubUrl: buildGithubDocUrl('pqet/index.md'),
  },
  'pqet-setup': {
    title: 'PQET Setup',
    navTitle: 'Setup',
    path: 'pqet/setup.md',
    sectionId: 'pqet',
    url: buildRawDocUrl('pqet/setup.md'),
    githubUrl: buildGithubDocUrl('pqet/setup.md'),
  },
} as const;

export type DocId = keyof typeof docsConfig;

export const DOCS_CONFIG: Record<DocId, DocEntry> = docsConfig;
export const DOC_IDS = Object.keys(docsConfig) as DocId[];

export const DOC_SECTIONS: DocSection[] = [
  {
    id: 'overview',
    title: 'Overview',
    docIds: [
      'overview-home',
      'overview-ai-evaluation-tool',
      'overview-docker-run',
      'overview-tdms',
      'overview-pqet',
    ],
  },
  {
    id: 'docker-setup',
    title: 'Docker Setup',
    docIds: ['docker-setup-home', 'docker-setup-config', 'docker-setup-gpu', 'docker-setup-run'],
  },
  {
    id: 'ai-evaluation-tool-cli',
    title: 'AI Evaluation Tool CLI',
    docIds: ['cli-home', 'cli-initial-setup', 'cli-gpu-setup', 'cli-importer-execution', 'cli-analysis-report'],
  },
  {
    id: 'tdms',
    title: 'TDMS',
    docIds: ['tdms-home', 'tdms-setup', 'tdms-access'],
  },
  {
    id: 'ai-evaluation-tool-ui',
    title: 'AI Evaluation Tool UI',
    docIds: ['ui-home', 'ui-setup', 'ui-dashboard'],
  },
  {
    id: 'pqet',
    title: 'PQET',
    docIds: ['pqet-home', 'pqet-setup'],
  },
];

const DOC_ID_BY_PATH = new Map<string, DocId>(
  DOC_IDS.map((docId) => [normalizeDocPath(DOCS_CONFIG[docId].path), docId])
);

export function normalizeDocPath(path: string) {
  return path.replace(/^\.?\//, '').replace(/^docs\//, '').replace(/\\/g, '/');
}

export function getDocIdByPath(path: string) {
  return DOC_ID_BY_PATH.get(normalizeDocPath(path)) ?? null;
}

export function getRepositoryRawUrl(repoPath: string) {
  return buildRawRepositoryUrl(repoPath);
}

export function getRepositoryGithubUrl(repoPath: string) {
  return buildGithubRepositoryUrl(repoPath);
}
