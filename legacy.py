import streamlit as st
from openai import OpenAI
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="คำถามมรดกชีวิต | Legacy Questions",
    page_icon="🕯️",
    layout="centered"
)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
MODEL = st.secrets.get("OPENAI_MODEL", "gpt-5.5")

st.title("🕯️ คำถามมรดกชีวิตสำหรับครอบครัวผู้ป่วยระยะประคับประคอง")
st.caption("เครื่องมือนี้ช่วยสร้างคำถามเพื่อพูดคุยอย่างอ่อนโยน ไม่ใช่การรักษาทางจิตเวช และไม่แทนบุคลากรสุขภาพ")

with st.expander("แนวคิด"):
    st.write("""
    คำถามมรดกชีวิตช่วยให้ผู้ป่วยและครอบครัวทบทวนชีวิต ความรัก ความภูมิใจ 
    สิ่งที่อยากฝากไว้ และความกังวลที่ยังค้างคา คล้ายแนวคิด dignity-centered care
    ในการดูแลแบบประคับประคอง
    """)

st.subheader("ข้อมูลเบื้องต้น")

role = st.selectbox(
    "ผู้ใช้คือใคร",
    ["ผู้ป่วย", "ลูก/หลาน", "คู่สมรส", "พ่อแม่", "พี่น้อง", "แพทย์/พยาบาล", "อาสาสมัคร", "อื่น ๆ"]
)

patient_stage = st.selectbox(
    "บริบทของผู้ป่วย",
    [
        "ยังสื่อสารได้ดี",
        "เหนื่อยง่าย พูดได้น้อย",
        "ใกล้ระยะท้ายมาก",
        "ครอบครัวต้องการเตรียมใจ",
        "หลังการสูญเสียแล้ว"
    ]
)

tone = st.selectbox(
    "โทนคำถามที่ต้องการ",
    ["อ่อนโยนมาก", "อบอุ่น", "ลึกซึ้ง", "สั้นและถามง่าย", "เหมาะกับคนไทย/ครอบครัวไทย"]
)

religious_style = st.selectbox(
    "แนวทางความเชื่อ",
    [
        "เป็นกลาง ไม่เน้นศาสนา",
        "พุทธแบบอ่อนโยน",
        "จิตวิญญาณแต่ไม่ศาสนา",
        "คริสต์",
        "อิสลาม",
        "ให้ผู้ใช้เลือกเอง"
    ]
)

main_goal = st.multiselect(
    "เป้าหมายของบทสนทนา",
    [
        "ทบทวนชีวิต",
        "บันทึกความทรงจำ",
        "ลดความกังวล",
        "ขออโหสิกรรม/ให้อภัย",
        "ฝากคำพูดถึงลูกหลาน",
        "เตรียมใจเรื่องความตาย",
        "ช่วยครอบครัวหลังสูญเสีย",
        "ทำสมุดมรดกชีวิต"
    ],
    default=["ทบทวนชีวิต", "ฝากคำพูดถึงลูกหลาน"]
)

risk_text = st.text_area(
    "มีประเด็นอารมณ์เสี่ยงหรือไม่ เช่น ไม่อยากอยู่ต่อ โทษตัวเองมาก นอนไม่ได้ ร้องไห้ทั้งวัน",
    height=100
)

extra_context = st.text_area(
    "บริบทเพิ่มเติม เช่น อายุ โรค ความสัมพันธ์ในครอบครัว สิ่งที่ผู้ป่วยรัก",
    height=140
)

st.divider()

def detect_high_risk(text: str) -> bool:
    red_flags = [
        "ฆ่าตัวตาย", "ไม่อยากอยู่", "อยากตาย", "ทำร้ายตัวเอง",
        "suicide", "kill myself", "self-harm", "hopeless"
    ]
    return any(flag.lower() in text.lower() for flag in red_flags)

def ask_gpt():
    now_bkk = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%Y-%m-%d %H:%M")

    system_prompt = """
คุณเป็นผู้ช่วยแพทย์และทีม palliative care ภาษาไทย
หน้าที่คือช่วยสร้างคำถาม legacy questions / dignity-centered questions
อย่างอ่อนโยน ปลอดภัย เคารพศักดิ์ศรีมนุษย์ และเหมาะกับบริบทครอบครัวไทย

ข้อกำหนด:
- อย่าทำเหมือนเป็นนักบำบัดแทนแพทย์
- อย่าเร่งให้ผู้ป่วยตอบเรื่องลึกเกินไป
- ให้คำถามสั้น ชัด ถามง่าย
- แบ่งระดับคำถาม: เริ่มต้น / ลึกขึ้น / ช่วงใกล้เสียชีวิต / หลังสูญเสีย
- มีคำแนะนำสำหรับญาติว่าควรถามอย่างไร
- มีคำเตือน red flags ที่ควรเรียกทีมสุขภาพทันที
- หลีกเลี่ยงการบอกว่า “ต้องปล่อยวาง” แบบกดดัน
- เน้น continuing bonds: ความรัก ความทรงจำ คุณค่า และคำฝากยังคงอยู่
"""

    user_prompt = f"""
สร้างชุดคำถามมรดกชีวิตภาษาไทยสำหรับ palliative care families

เวลา BKK: {now_bkk}
ผู้ใช้คือ: {role}
บริบทผู้ป่วย: {patient_stage}
โทน: {tone}
แนวทางความเชื่อ: {religious_style}
เป้าหมาย: {", ".join(main_goal)}
ประเด็นอารมณ์เสี่ยง: {risk_text}
บริบทเพิ่มเติม: {extra_context}

ขอ output เป็นหัวข้อ:
1. คำแนะนำก่อนเริ่มคุย
2. คำถามเริ่มต้น 10 ข้อ
3. คำถามลึกขึ้น 10 ข้อ
4. คำถามสำหรับฝากถึงลูกหลาน/คนรัก 10 ข้อ
5. คำถามลดความกังวลและสิ่งค้างคา 10 ข้อ
6. ถ้าผู้ป่วยเหนื่อยมาก ให้ถามแบบสั้นมาก 10 ข้อ
7. แนวทางหลังผู้ป่วยเสียชีวิตสำหรับครอบครัว
8. Red flags ที่ควรติดต่อแพทย์/พยาบาล/ฉุกเฉิน
"""

    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.output_text

if st.button("สร้างคำถามมรดกชีวิต", type="primary"):
    if detect_high_risk(risk_text):
        st.error("""
        พบข้อความที่อาจเสี่ยงต่อการทำร้ายตนเองหรือสิ้นหวังรุนแรง  
        กรุณาติดต่อแพทย์/พยาบาลทันที หรือสายด่วนสุขภาพจิต 1323  
        หากมีอันตรายเฉียบพลัน โทร 1669
        """)

    with st.spinner("กำลังสร้างคำถามอย่างอ่อนโยน..."):
        try:
            result = ask_gpt()
            st.session_state["result"] = result
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

if "result" in st.session_state:
    st.subheader("ผลลัพธ์")
    st.markdown(st.session_state["result"])

    filename = f"legacy_questions_{datetime.now(ZoneInfo('Asia/Bangkok')).strftime('%Y%m%d_%H%M')}.txt"
    st.download_button(
        "ดาวน์โหลดเป็นไฟล์ .txt",
        data=st.session_state["result"],
        file_name=filename,
        mime="text/plain"
    )

st.divider()

st.info("""
ข้อควรระวัง: หากผู้ป่วยหรือญาติมีอาการสิ้นหวังรุนแรง พูดถึงการตายซ้ำ ๆ แบบต้องการทำร้ายตนเอง 
นอนไม่ได้หลายคืน สับสน กระวนกระวายมาก หรือมีความเสี่ยงฉุกเฉิน ควรส่งต่อทีมสุขภาพทันที
""")