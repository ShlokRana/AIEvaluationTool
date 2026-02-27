import os
from dotenv import load_dotenv
import json
import ast
import csv
from .logger import get_logger
from types import SimpleNamespace
import hashlib
from deepeval.metrics.g_eval.schema import Steps, ReasonScore
from ollama import Client, AsyncClient
from deepeval.models.base_model import DeepEvalBaseLLM
from typing import Optional, List

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics

logger = get_logger("utils_new")

class FileLoader:
    """
    run_file_path : should be the __file__
    """
    @staticmethod
    def _load_env_vars(run_file_path:str):
        env_path = os.path.join(os.path.dirname(run_file_path), '.env')
        # check if the .env file exists
        if not os.path.exists(env_path):
            logger.error(f"Could not find the .env file at path : {env_path}. Please make sure to create one and add the required environment variables.")
            exit(1)
        else:
            load_dotenv(env_path)
    
    @staticmethod
    def _load_file_content(run_file_path:str, req_folder_path:str = "", file_name:str = "", **kwargs):
        data_dir = os.path.join(os.path.dirname(run_file_path), req_folder_path) if req_folder_path != '' else os.path.dirname(run_file_path)
        try:
            file_names = os.listdir(data_dir)
        except:
            file_names = list()
            logger.error(f"The path {data_dir} does not exist.")
        file_content = {}
        if file_name != "":
            file_content = FileLoader._fill_values(file_content, data_dir, file_name, multiple=False) # multiple false means only one file
            return file_content
        else:
            strat = kwargs.get("strategy_name")
            if not strat:
                logger.error("Strategy_name was not inilialized.")
                return file_content
            else:
                prefixes = [os.path.commonprefix([strat, f]) for f in file_names]
                longest = max(prefixes, key=len, default=None)
                files = [f for f in file_names if f.startswith(longest) and len(longest) >= len(strat.split("_")[0])] #the length of the prefix should be at least as long as the first word in the strategy name so that longest is not empty, if its empty it matches with all the names
                if len(files) > 0:
                    for f in files:
                        logger.info(f"Using file {f} to load the examples and evaluate the strategy.")
                        file_content = FileLoader._fill_values(file_content, data_dir, f)
                else:
                    logger.error("None of the files in the data/examples directory match the strategy name.")
        return file_content

    @staticmethod
    def _fill_values(file_content:dict, data_dir:str, f:str, multiple:bool = True):
        store_name = f.split(".")[0]
        if(f.split(".")[1] == "json"):
            with open(os.path.join(data_dir, f), "r") as file:
                content = json.load(file)
                if isinstance(content, dict) and not multiple:
                    file_content = content
                else:
                    file_content[store_name] = content
        elif(f.split(".")[1] == "txt"):
            with open(os.path.join(data_dir, f), "r") as file:
                file_content[store_name] = ast.literal_eval(file.read())
        return file_content


    @staticmethod
    def _check_if_present(run_file_path:str, folder_path:str, search_file_name:str):
        if (os.path.exists(os.path.join(os.path.join(os.path.dirname(run_file_path), folder_path), search_file_name))):
            return True
        else:
            return False
    
    @staticmethod
    def _save_values(run_file_path:str, data:dict, data_dir:str, file_name:str):
        ext = file_name.split(".")[1]
        run_file_dir = os.path.dirname(run_file_path)
        with open(os.path.join(os.path.join(run_file_dir, data_dir), file_name), "w") as f:
            if ext == "json":
                json.dump(data, f)
            elif ext == "txt":
                f.write(json.dumps(data))

    @staticmethod
    def dot_dict(d):
        if isinstance(d, dict):
            return SimpleNamespace(**{k : FileLoader.dot_dict(v) for k,v in d.items()})
        else:
            return d

    @staticmethod
    def _to_dot_dict(run_file_path:str, dir_file_path:str, **kwargs):
        full_path = os.path.join(os.path.dirname(run_file_path), dir_file_path)
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                data = json.load(f)
            if kwargs.get("simple"):
                def hook(obj):
                    if obj.get("__as_dict__") is True:
                        obj.pop("__as_dict__", None)
                        return obj
                    return SimpleNamespace(**obj)
                return json.loads(json.dumps(data[kwargs.get("strat_name")]), object_hook=hook)
            else:
                return FileLoader.dot_dict(data)
        else:
            logger.error(f"[ERROR] : could not find the path specified : {full_path}")
            return {}
    
    @staticmethod
    def _save_to_csv(run_file_path:str, df:dict, **kwargs):
        folder_path = os.path.join(os.path.dirname(run_file_path), os.path.join(kwargs.get("data_dir"), kwargs.get("save_dir")) )
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        file_path = os.path.join(folder_path, f"{kwargs.get('strat_name')}.csv")
        file_exists = os.path.isfile(file_path)
        hash = hashlib.sha256(df.get("id").encode('utf-8')).hexdigest()[:20]

        if file_exists:
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fields = reader.fieldnames     
                data = {row["id"] : row for row in reader}
            values = [hash, *df.get("score").values()]
            data.update({hash : {f : v for f, v in zip(fields, values)}}) 
        else:
            fields = ["id", *df.get("score").keys()]
            values = [hash, *df.get("score").values()]
            data = {hash : {f : v for f, v in zip(fields, values)}}

        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data.values())
        logger.info(f"Score and reason saved to : {file_path}")

class CustomOllamaModel(DeepEvalBaseLLM):
    def __init__(self, model_name : str, url : str, *args, **kwargs):
        self.model_name = model_name
        self.ollama_url = f"{url.rstrip()}"
        self.ollama_client = Client(host=self.ollama_url)
        self.score_reason = None
        self.steps = None
    
    def generate(self, input : str, *args, **kwargs) -> str:
        messages = [{"role": "user", "content": f'{input} /nothink'}] # nothink allows us to only get the final answer
        response = self.ollama_client.chat(
            model = self.model_name,
            messages=messages,
            format="json"
        )
        raw = json.loads(response.message.content)
        schema_ =  kwargs.get("schema")(**raw) # the deepeval library uses different schemas to serialize the JSON, so we return the schemas as required by the library
        if(kwargs.get("schema") is ReasonScore):
            self.score_reason = {"Score": schema_.score, "Reason": schema_.reason}
        if(kwargs.get("schema") is Steps):
            self.steps = schema_.steps
        return schema_ 
    
    def load_model(self, *args, **kwargs):
        return None
    
    async def a_generate(self, input:str, *args, **kwargs):
        client = AsyncClient(host=self.ollama_url)
        messages = [{"role": "user", "content": f'{input} /nothink'}]
        response = await client.chat(
            model=self.model_name,
            messages=messages,
            format="json"
        )
        raw = json.loads(response.message.content)
        schema_ =  kwargs.get("schema")(**raw)
        if(kwargs.get("schema") is ReasonScore):
            self.score_reason = {"Score": schema_.score, "Reason": schema_.reason}
        if(kwargs.get("schema") is Steps):
            self.steps = {"Steps" : schema_.steps}
        return schema_
    
    def get_model_name(self, *args, **kwargs):
        return self.model_name


class OllamaConnect:
    
    FileLoader._load_env_vars(__file__)
    ollama_url = os.getenv("OLLAMA_URL")
    dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="ollama_comms")

    @staticmethod
    def prompt_model(text:str, fields:List[str], model_names:List[str] = None, options:dict = None) -> List[dict]:
        ollama_client = Client(host=OllamaConnect.ollama_url)
        tries = OllamaConnect.dflt_vals.n_tries
        resp_in_format = []
        models = OllamaConnect.dflt_vals.model_names if model_names is None else model_names
        while(resp_in_format == [] and tries > 0):
            for model in models:
                try:
                    inputs = {
                        "model" : model,
                        "messages" : [
                            {
                                "role" : "user",
                                "content" : f"{text} /nothink",
                            }
                        ],
                        "format":"json",
                    }
                    if options is not None:
                        inputs.update({"options": options})
                    response = ollama_client.chat(**inputs)
                    try:
                        final = json.loads(response.message.content)
                    except:
                        final = {}
                except Exception as e:
                    logger.error(f"Did not receive any response from the model : {model}.")
                    final = {}
                if(OllamaConnect.has_correct_format(final, fields)):
                    resp_in_format.append(final)
                else:
                    logger.error("Response does not contain the required fields or is not in the correct format.")
            tries -= 1
        return resp_in_format
    
    @staticmethod
    def has_correct_format(obj : Optional[dict], fields: List[str]):
        correct = isinstance(obj, dict)
        distinct_set = set(list(obj.keys())).intersection(set(fields))
        if len(distinct_set) > 0:
            for fld in distinct_set:
                correct = correct and fld in fields and isinstance(obj.get(fld), str) 
            return correct
        else:
            return False
    
    @staticmethod
    def get_reason(agent_response:str, strategy_name:str, score:float, **kwargs):
        prompt = OllamaConnect.dflt_vals.reason_prompt.format(input_sent=agent_response, metric=strategy_name, score=score, add_info=kwargs.get("add_info", ""))
        responses = OllamaConnect.prompt_model(prompt, OllamaConnect.dflt_vals.reqd_flds)
        final_rsn = ""
        if(len(responses) > 0):
            reasons = [r["reason"] for r in responses]
            if(len(reasons) == 1): return f"{reasons[0]}" 
            for i, r in enumerate(reasons):
                if i == 0:
                    final_rsn += f"Reason {i+1} : {r}"
                else:
                    final_rsn += f"\n\n Reason {i+1} : {r}"
            return final_rsn
        else:
            return "Could not get a proper reasoning for the score."
        
    @staticmethod
    def get_metric_summary(metric_name: str, scores, reasons=None, **kwargs):
        """
        Accepts a list of scores (and optional reasons) for one metric
        and produces a single coherent summary at metric level.
        """

        # --- Normalize scores ---
        values = list(scores) if isinstance(scores, (list, tuple)) else [scores]

        avg_score = round(sum(values) / len(values), 3)
        score_text = f"Average: {avg_score} from {len(values)} samples"

        # --- Prepare reasons block ---
        reason_text = ""
        if reasons:
            items = reasons if isinstance(reasons, (list, tuple)) else [reasons]
            reason_text = "\n".join(f"- {r}" for r in items if r)

        # --- Build prompt ---
        prompt = OllamaConnect.dflt_vals.metric_summary_prompt.format(
            metric=metric_name,
            scores=score_text,
            reasons=reason_text,
            add_info=kwargs.get("add_info", "")
        )

        # --- Call model ---
        responses = OllamaConnect.prompt_model(
            prompt,
            OllamaConnect.dflt_vals.reqd_flds
        )

        if not responses:
            return "Could not generate metric summary."

        summaries = [r["summary"] for r in responses]

        return summaries[0] if len(summaries) == 1 else "\n\n".join(
            f"Summary {i+1} : {s}" for i, s in enumerate(summaries)
        )


    @staticmethod
    def get_single_plan_summary(plan_name: str, metrics: dict, **kwargs):

        plan_overview = []

        for metric_name, data in metrics.items():

            if "metric_summary" not in data:
                continue

            plan_overview.append({
                "metric": metric_name,
                "metric_summary": data.get("metric_summary"),
                "testcase_count": len(data.get("Testcases", {}))
            })

        prompt = OllamaConnect.dflt_vals.plan_summary_prompt.format(
            plan=plan_name,
            overview=json.dumps(plan_overview, indent=2),
            add_info=kwargs.get("add_info", "")
        )

        responses = OllamaConnect.prompt_model(
            prompt,
            OllamaConnect.dflt_vals.reqd_flds
        )

        return responses[0]["summary"] if responses else "Could not generate plan summary."
        
    @staticmethod
    def get_run_summary(score_card: dict, **kwargs):

        run_overview = []

        for plan_name, metrics in score_card.items():

            if not isinstance(metrics, dict) or plan_name == "PlanSummary":
                continue

            # Grab plan summary from any metric node (they all share it)
            plan_summary = None
            for data in metrics.values():
                if "plan_summary" in data:
                    plan_summary = data["plan_summary"]
                    break

            if not plan_summary:
                continue

            run_overview.append({
                "plan": plan_name,
                "plan_summary": plan_summary
            })

        prompt = OllamaConnect.dflt_vals.run_summary_prompt.format(
            overview=json.dumps(run_overview, indent=2),
            add_info=kwargs.get("add_info", "")
        )

        responses = OllamaConnect.prompt_model(
            prompt,
            OllamaConnect.dflt_vals.reqd_flds
        )

        if not responses:
            return "Could not generate run summary."

        summaries = [r["summary"] for r in responses]

        return summaries[0] if len(summaries) == 1 else "\n\n".join(
            f"Summary {i+1} : {s}" for i, s in enumerate(summaries)
        )


# The EvaluationReport class is responsible for generating a PDF report of the evaluation results. 
class EvaluationReport:
    def __init__(self, title="Conversational AI Evaluation Report",
                 pagesize=A4, margin_mm=15):

        self.title = title
        self.pagesize = pagesize
        self.margin = margin_mm * mm
        self.styles = getSampleStyleSheet()

        # Section heading
        self.styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=self.styles["Heading2"],
                fontSize=12,
                leading=14,
                spaceAfter=6
            )
        )

        # Left aligned labels for key column
        self.styles.add(
            ParagraphStyle(
                name="BodyLabel",
                parent=self.styles["BodyText"],
                fontSize=10,
                leading=12,
                alignment=0,        # TA_LEFT
                spaceAfter=2
            )
        )

        # Justified body text
        self.styles.add(
            ParagraphStyle(
                name="Body",
                parent=self.styles["BodyText"],
                fontSize=10,
                leading=12,
                alignment=TA_JUSTIFY,
                spaceAfter=4
            )
        )

    # -----------------------------------------------------

    def _draw_header(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 14)

        page_width = self.pagesize[0]
        canvas.drawCentredString(
            page_width / 2.0,
            self.pagesize[1] - self.margin + 6 * mm,
            self.title
        )

        canvas.restoreState()

    # -----------------------------------------------------

    def section_title(self, text):
        return Paragraph(text, self.styles["SectionTitle"])

    def body_text(self, text):
        return Paragraph(text, self.styles["Body"])

    # -----------------------------------------------------

    def key_value_table(self, kv_pairs):
        left_w = 40 * mm
        right_w = self.pagesize[0] - 2 * self.margin - left_w

        data = [
            [
                Paragraph(f"<b>{k}:</b>", self.styles["BodyLabel"]),
                Paragraph(str(v), self.styles["Body"])
            ]
            for k, v in kv_pairs
        ]

        t = Table(data, colWidths=[left_w, right_w], hAlign="LEFT")

        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))

        return t

    # -----------------------------------------------------

    def score_table(self, headers, rows, column_widths=None):

        usable_width = self.pagesize[0] - 2 * self.margin
        font_name = "Helvetica"
        font_size = 10

        col_count = len(headers)

        # -----------------------------------------------------
        # CASE 1: Custom column widths provided
        # -----------------------------------------------------
        if column_widths:

            if len(column_widths) != col_count:
                raise ValueError("column_widths must match number of headers")

            colWidths = []

            auto_indices = []
            fixed_total = 0

            for i, w in enumerate(column_widths):
                if w is None:
                    colWidths.append(None)
                    auto_indices.append(i)
                else:
                    colWidths.append(w)
                    fixed_total += w

            remaining_width = usable_width - fixed_total

            if remaining_width <= 0:
                raise ValueError("Fixed column widths exceed usable page width")

            # Distribute remaining width equally among auto columns
            if auto_indices:
                auto_width = remaining_width / len(auto_indices)
                for i in auto_indices:
                    colWidths[i] = auto_width

        # -----------------------------------------------------
        # CASE 2: Auto-sizing mode
        # -----------------------------------------------------
        else:

            data_raw = [headers] + rows
            max_widths = [0] * col_count

            for row in data_raw:
                for i, cell in enumerate(row):
                    text = str(cell)
                    text_width = pdfmetrics.stringWidth(text, font_name, font_size)
                    max_widths[i] = max(max_widths[i], text_width)

            padding_buffer = 20
            colWidths = [w + padding_buffer for w in max_widths]

            total_width = sum(colWidths)

            if total_width > usable_width:
                scale = usable_width / total_width
                colWidths = [w * scale for w in colWidths]

            MIN_COL_WIDTH = 40
            colWidths = [max(w, MIN_COL_WIDTH) for w in colWidths]

            total_width = sum(colWidths)
            if total_width > usable_width:
                scale = usable_width / total_width
                colWidths = [w * scale for w in colWidths]

        # -----------------------------------------------------
        # Build table
        # -----------------------------------------------------
        formatted_data = [
            [Paragraph(f"<b>{h}</b>", self.styles["Body"]) for h in headers]
        ]

        for r in rows:
            formatted_data.append([
                Paragraph(str(cell), self.styles["Body"])
                for cell in r
            ])

        table = Table(
            formatted_data,
            colWidths=colWidths,
            repeatRows=1,
            hAlign="LEFT",
            splitByRow=1
        )

        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("WORDWRAP", (0, 0), (-1, -1), "CJK"),
        ]))

        return table


    # -----------------------------------------------------

    def scorecard_to_table(self, score_card):
        # Count actual plans (exclude PlanSummary meta key if present)
        plan_names = [p for p in score_card.keys() if p != "PlanSummary"]
        multiple_plans = len(plan_names) > 1

        # Build headers dynamically
        headers = [
            "Plan Name",
            "Metric Name",
            "Score (0-1)",
            "Metric Summary",
        ]

        if multiple_plans:
            headers.append("Plan Summary")

        rows = []

        for plan_name in plan_names:

            metrics = score_card[plan_name]
            first_metric = True

            for metric_name, metric_data in metrics.items():

                metric_score = metric_data.get("metric_score", "")
                metric_summary = metric_data.get("metric_summary", "")
                plan_summary = metric_data.get("plan_summary", "")

                row = [
                    plan_name,
                    metric_name,
                    str(metric_score),
                    metric_summary,
                ]

                # Only include plan summary column if multiple plans exist
                if multiple_plans:
                    row.append(plan_summary if first_metric else "")

                rows.append(row)

                first_metric = False

        return headers, rows


    # -----------------------------------------------------

    @classmethod
    def create_report(
        cls,
        target_name: str,
        run_name: str,
        timestamp: str,
        total_testcases: int,
        target_summary: str,
        score_card: dict,
        plan_summary: str = None,
        out_path: str = None,
        column_widths: list = None 
    ):

        inst = cls()

        filename = out_path or f"AI_Evaluation_Report_{target_name}.pdf"

        doc = SimpleDocTemplate(
            filename,
            pagesize=inst.pagesize,
            leftMargin=inst.margin,
            rightMargin=inst.margin,
            topMargin=inst.margin,
            bottomMargin=inst.margin,
        )

        story = []

        story.append(inst.section_title("Experiment Overview"))

        kv = [
            ("Target Name", target_name),
            ("Run Name", run_name),
            ("Timestamp", timestamp),
            ("Total Test Cases", str(total_testcases)),
        ]

        story.append(inst.key_value_table(kv))
        story.append(Spacer(1, 8))

        has_run_summary = any(
            metric.get("run_summary")
            for plan in score_card.values()
            for metric in plan.values()
            if isinstance(metric, dict)
        )

        section_title = (
            "Target Evaluation Run Summary"
            if has_run_summary
            else "Target Evaluation Plan Summary"
        )

        story.append(inst.section_title(section_title))

        if has_run_summary:
            story.append(inst.body_text(target_summary))
        elif plan_summary:
            story.append(inst.body_text(plan_summary))
        else:
            story.append(inst.body_text("No summary available."))

        story.append(Spacer(1, 8))

        story.append(inst.section_title("Scores Table"))

        headers, rows = inst.scorecard_to_table(score_card)
        story.append(inst.score_table(headers, rows, column_widths=column_widths))

        doc.build(
            story,
            onFirstPage=inst._draw_header,
            onLaterPages=inst._draw_header
        )

        return filename
