import os

from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langchain.schema import HumanMessage
from langchain_core.prompts import PromptTemplate

from api_config import api_config

api_key = api_config.get_api_key()
os.environ["DASHSCOPE_API_KEY"] = os.getenv("DASHSCOPE_API_KEY")


class Agent:
    def __init__(self, medical_report=None, role=None, extra_info=None):
        self.medical_report = medical_report
        self.role = role
        self.extra_info = extra_info or {}
        self.prompt_template = self.create_prompt_template()
        self.model = ChatTongyi(
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
            model="qwen-plus",
            temperature=0.3
        )

    def create_prompt_template(self):
        if self.role == "MultidisciplinaryTeam":
            # template = """
            #     Act like a multidisciplinary team of healthcare professionals.
            #     You will receive medical reports from a Cardiologist, Psychologist, and Pulmonologist.
            #     Task: Analyze the reports and generate a list of 3 possible health issues with explanations.
            #
            #     Cardiologist Report: {cardiologist_report}
            #     Psychologist Report: {psychologist_report}
            #     Pulmonologist Report: {pulmonologist_report}
            # """
            template = """
                请用中文回答以下问题。
                请扮演一个由心脏科医生、心理医生和肺病专家组成的多学科医疗团队。
                你将收到来自这三位专家的医学报告。
                任务：分析这些报告，并生成3个可能的健康问题及其解释。

                心脏科报告: {cardiologist_report}
                心理科报告: {psychologist_report}
                呼吸科报告: {pulmonologist_report}
            """

            return PromptTemplate.from_template(template)
        else:
            # templates = {
            #     "Cardiologist": """
            #         Act like a cardiologist. You will receive a medical report of a patient.
            #         Task: Review the patient's cardiac workup, including ECG, blood tests, Holter monitor results, and echocardiogram.
            #         Focus: Identify subtle signs of cardiac issues that could explain the patient’s symptoms.
            #         Recommendation: Provide possible causes and next steps.
            #         Medical Report: {medical_report}
            #     """,
            #     "Psychologist": """
            #         Act like a psychologist. You will receive a patient's report.
            #         Task: Identify potential mental health issues like anxiety, depression, or trauma.
            #         Recommendation: Provide insights and recommended next steps.
            #         Medical Report: {medical_report}
            #     """,
            #     "Pulmonologist": """
            #         Act like a pulmonologist. You will receive a patient's report.
            #         Task: Identify possible respiratory issues such as asthma, COPD, or lung infections.
            #         Recommendation: Suggest possible causes and further tests.
            #         Medical Report: {medical_report}
            #     """
            # }
            templates = {
                "Cardiologist": """
                    请用中文回答以下问题。
                    请扮演一位心脏病专家，你将收到一份病人的医学报告。
                    任务：审查患者的心脏检查结果，包括心电图、血液检查、动态心电图和超声心动图。
                    重点：识别可能解释患者症状的细微心脏问题。
                    建议：提供可能的病因和下一步建议。
                    医学报告: {medical_report}
                """,
                "Psychologist": """
                    请用中文回答以下问题。
                    请扮演一位心理医生，你将收到一份患者的医学报告。
                    任务：识别潜在的心理健康问题，如焦虑、抑郁或创伤。
                    建议：提供专业见解和后续建议。
                    医学报告: {medical_report}
                """,
                "Pulmonologist": """
                    请用中文回答以下问题。
                    请扮演一位肺病专家，你将收到一份患者的医学报告。
                    任务：识别可能的呼吸系统问题，如哮喘、慢阻肺或肺部感染。
                    建议：提出可能的病因和建议进一步检查。
                    医学报告: {medical_report}
                """
            }

            return PromptTemplate.from_template(templates[self.role])

    def run(self):
        print(f"{self.role} is running...")

        if self.role == "MultidisciplinaryTeam":
            formatted_prompt = self.prompt_template.format(
                cardiologist_report=self.extra_info.get("cardiologist_report", ""),
                psychologist_report=self.extra_info.get("psychologist_report", ""),
                pulmonologist_report=self.extra_info.get("pulmonologist_report", "")
            )
        else:
            formatted_prompt = self.prompt_template.format(medical_report=self.medical_report)

        try:
            response = self.model.invoke([HumanMessage(content=formatted_prompt)])
            return response.content
        except Exception as e:
            print("Error occurred:", e)
            return None


# Define specialized agent classes
class Cardiologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Cardiologist")


class Psychologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Psychologist")


class Pulmonologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Pulmonologist")


class MultidisciplinaryTeam(Agent):
    def __init__(self, cardiologist_report, psychologist_report, pulmonologist_report):
        extra_info = {
            "cardiologist_report": cardiologist_report,
            "psychologist_report": psychologist_report,
            "pulmonologist_report": pulmonologist_report
        }
        super().__init__(role="MultidisciplinaryTeam", extra_info=extra_info)
