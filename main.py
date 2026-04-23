import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import re
from datetime import datetime

# ================= 1. 설정 섹션 =================
# Render의 Environment Variables에서 가져오도록 수정
token = os.environ.get('DISCORD_TOKEN')

# 주요 채널 ID
log_channel_id = 1476797018512035850           # 뉴페기록
admin_list_channel_id = 1476833479626068060     # 관리자명단 고정 채널
CREATION_CHANNEL_ID = 1482715049343717519      # 1인방 생성 채널 (음성)
NICKNAME_CHANGE_CHANNEL_ID = 1483015181742375042 # 닉네임변경 채널 ID

# 사진 스레드 자동 생성 채널 리스트
THREAD_CHANNELS = [
    1483339099627589794, 1483339195408711752, 1483339340729028698,
    1483339765146325133, 1483338780491513947
]

# 주요 역할 ID
OPERATOR_ROLE_ID = 1493074942697410650          # 운영진
GUIDE_LEADER_ROLE_ID = 1475383177358086194      # 안내팀장
VACANCY_ROLE_ID = 1493076970785738775           # 공석 역할
SEOLYA_ROLE_ID = 1475273285473145015            # 설야
BAEKYA_ROLE_ID = 1475273106095476938            # 백야
VICE_PRESIDENT_ROLE_ID = 1493064382819729620    # 부대표
MANAGER_ROLE_ID = 1490297934439252181           # 매니저
DEPT_ADMIN_ROLE_ID = 1490293227088121976        # 부서관리자
INTERN_ROLE_ID = 1479129998982905996            # 인턴

DATA_FILE = "guide_stats.json"

# 부서별 데이터 구조
DEPT_DATA = {
    "보안": {"팀장": 1475383159091630132, "부팀장": 1475386153497530368, "팀원": 1475270914055864441},
    "총무": {"팀장": 1475383056201416746, "부팀장": 1475386094412365916, "팀원": 1475271041805713578},
    "안내": {"팀장": 1475383177358086194, "부팀장": 1475386174477566022, "팀원": 1475271206042337452},
    "뉴관": {"팀장": 1475383200493867008, "부팀장": 1475386199823614157, "팀원": 1475271334195101857},
    "홍보": {"팀장": 1475383221280571524, "부팀장": 1475386219574591529, "팀원": 1475271399471059165},
    "기획": {"팀장": 1475383244429070387, "부팀장": 1475386239183097957, "팀원": 1475271558619725905},
    "내전": {"팀장": 1475383263592845332, "부팀장": 1475386273211613225, "팀원": 1475271613854388384}
}

ROLES_LIST = {
    "대표": 1475269649754230904, "부대표": VICE_PRESIDENT_ROLE_ID, "매니저": MANAGER_ROLE_ID,
    "부서관리자": DEPT_ADMIN_ROLE_ID, "인턴": INTERN_ROLE_ID, "설야관리자": 1475272064234553456,
    "디자이너": 1475271676227883179, "미인증": 1476347134881042643, "백야": BAEKYA_ROLE_ID, "설야": SEOLYA_ROLE_ID,
    "남자": 1475273515329388705, "여자": 1475273626847547452,
    "age": {
        "13": 1475387427513303141, "12": 1491551091916148928, "11": 1475387480998936708,
        "10": 1475387507335106600, "09": 1475387525169152050, "08": 1475387549148119222,
        "07": 1475387563907874846, "06": 1475387584875331594, "05": 1475387610300944394,
        "04": 1475387624498790471, "03": 1475387638973337821, "02": 1475387652520939653,
        "01": 1475387669059080335, "00": 1475387695630123114, "99": 1475387709588508824,
        "98": 1475387732111917180, "97": 1475387758292762624, "비공": 1477536928864796673
    }
}

temp_channels = {}

# ================= 2. 유틸리티 함수 =================
def load_stats():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_stats(stats):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(stats, f, ensure_ascii=False, indent=4)

def get_final_nickname(member, name_input):
    user_role_ids = [r.id for r in member.roles]
    if VICE_PRESIDENT_ROLE_ID in user_role_ids: return name_input
    if MANAGER_ROLE_ID in user_role_ids: return f"! {name_input}"
    if DEPT_ADMIN_ROLE_ID in user_role_ids: return f"& {name_input}"
    for dept_name, roles in DEPT_DATA.items():
        if roles["팀장"] in user_role_ids: return f"『 {dept_name}팀장 』 {name_input}"
        if roles["부팀장"] in user_role_ids: return f"『 {dept_name}부팀장 』 {name_input}"
        if roles["팀원"] in user_role_ids:
            if INTERN_ROLE_ID in user_role_ids: return f"『 {dept_name}인턴 』 {name_input}"
            return f"『 {dept_name}팀 』 {name_input}"
    if 1475271676227883179 in user_role_ids: return f"『 디자이너 』 {name_input}"
    if BAEKYA_ROLE_ID in user_role_ids: return f"『 백야 』 {name_input}"
    elif SEOLYA_ROLE_ID in user_role_ids: return f"『 설야 』 {name_input}"
    return None

# ================= 3. 메인 봇 클래스 =================
class SeolyaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self):
        await self.tree.sync()

bot = SeolyaBot()

@bot.event
async def on_ready():
    print(f"✅ 로그인 성공: {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id == NICKNAME_CHANGE_CHANNEL_ID:
        name_input = message.content.strip()
        if re.fullmatch(r'[가-힣]{1,8}', name_input):
            final_nick = get_final_nickname(message.author, name_input)
            if final_nick:
                try:
                    if message.author.display_name != final_nick:
                        await message.author.edit(nick=final_nick)
                    await message.add_reaction("✅")
                except: await message.add_reaction("❌")
            else: await message.add_reaction("❌")
        else: await message.add_reaction("❌")
        return
    if message.channel.id in THREAD_CHANNELS:
        if message.attachments:
            if any(att.content_type and att.content_type.startswith('image') for att in message.attachments):
                try: await message.create_thread(name=f"{message.author.display_name}님의 기록")
                except: pass
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == CREATION_CHANNEL_ID:
        guild = member.guild
        category = after.channel.category
        seolya_role = guild.get_role(SEOLYA_ROLE_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
            seolya_role: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=False),
            member: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=False, move_members=True)
        }
        channel_name = f"₊˚ 🌨️ ⊹ {member.display_name}님의 채널 ꒷꒦"
        new_channel = await guild.create_voice_channel(name=channel_name, category=category, overwrites=overwrites, user_limit=1)
        await member.move_to(new_channel)
        temp_channels[new_channel.id] = member.id
    if before.channel and before.channel.id in temp_channels:
        if len(before.channel.members) == 0:
            try:
                await before.channel.delete()
                del temp_channels[before.channel.id]
            except: pass

@bot.tree.command(name="명단업데이트", description="운영진 전용: 관리자 명단을 최신화합니다.")
async def update_admin_list(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if not any(role.id == OPERATOR_ROLE_ID for role in interaction.user.roles):
        return await interaction.followup.send("❌ 권한 없음.")
    guild = interaction.guild
    def get_role_mentions(role_id, filter_members=None):
        role = guild.get_role(role_id)
        if not role: return f"<@&{VACANCY_ROLE_ID}>"
        members = role.members
        if filter_members: members = [m for m in members if m in filter_members]
        return ", ".join([m.mention for m in members]) if members else f"<@&{VACANCY_ROLE_ID}>"
    lines = [f"<@&{ROLES_LIST['대표']}> : {get_role_mentions(ROLES_LIST['대표'])}",
             f"<@&{ROLES_LIST['부대표']}> : {get_role_mentions(ROLES_LIST['부대표'])}",
             f"<@&{ROLES_LIST['매니저']}> : {get_role_mentions(ROLES_LIST['매니저'])}\n"]
    for d in ["총무", "보안", "안내", "뉴관", "홍보", "기획", "내전"]:
        team_role = guild.get_role(DEPT_DATA[d]["팀원"])
        team_m = team_role.members if team_role else []
        lines.append(f"{d}팀 담당 <@&{ROLES_LIST['부서관리자']}> : {get_role_mentions(ROLES_LIST['부서관리자'], team_m)}")
        lines.append(f"<@&{DEPT_DATA[d]['팀장']}> : {get_role_mentions(DEPT_DATA[d]['팀장'])}")
        lines.append(f"<@&{DEPT_DATA[d]['부팀장']}> : {get_role_mentions(DEPT_DATA[d]['부팀장'])}")
        excl_ids = [DEPT_DATA[d]["팀장"], DEPT_DATA[d]["부팀장"], DEPT_ADMIN_ROLE_ID, INTERN_ROLE_ID]
        staff = ", ".join([m.mention for m in team_m if not any(r.id in excl_ids for r in m.roles)])
        lines.append(f"<@&{DEPT_DATA[d]['팀원']}> : {staff if staff else f'<@&{VACANCY_ROLE_ID}>'}")
        lines.append(f"<@&{INTERN_ROLE_ID}> : {get_role_mentions(INTERN_ROLE_ID, team_m)}\n")
    embed = discord.Embed(title="❄️ 설야 서버 관리자 명단", description="\n".join(lines), color=0x2b2d31)
    embed.set_footer(text=f"업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    channel = bot.get_channel(admin_list_channel_id)
    target = None
    async for m in channel.history(limit=5):
        if m.author == bot.user: target = m; break
    if target: await target.edit(embed=embed)
    else: await channel.send(embed=embed)
    await interaction.followup.send("✅ 완료.")

@bot.tree.command(name="팀합격", description="팀장 전용: 인턴 및 부서 역할 지급.")
async def team_pass(interaction: discord.Interaction, 대상자: discord.Member):
    u_roles = [r.id for r in interaction.user.roles]
    mapping = {
        DEPT_DATA["총무"]["팀장"]: [DEPT_DATA["총무"]["팀원"], INTERN_ROLE_ID, 1475272064234553456],
        DEPT_DATA["보안"]["팀장"]: [DEPT_DATA["보안"]["팀원"], INTERN_ROLE_ID, 1475272064234553456, 1478940437833187459],
        DEPT_DATA["안내"]["팀장"]: [DEPT_DATA["안내"]["팀원"], INTERN_ROLE_ID, 1475272064234553456, 1478940277853917375],
        DEPT_DATA["뉴관"]["팀장"]: [DEPT_DATA["뉴관"]["팀원"], INTERN_ROLE_ID, 1475272064234553456, 1478940393255993448]
    }
    found = next((mapping[rid] for rid in mapping if rid in u_roles), None)
    if not found: return await interaction.response.send_message("❌ 팀장 권한 필요.", ephemeral=True)
    await 대상자.add_roles(*[interaction.guild.get_role(rid) for rid in found if interaction.guild.get_role(rid)])
    await interaction.response.send_message(f"✅ {대상자.mention}님 합격 처리가 완료되었습니다.", ephemeral=True)

@bot.tree.command(name="역할지급", description="안내팀 전용: 뉴페 가이드.")
async def give_roles(interaction: discord.Interaction, 유저: discord.Member, 이름: str, 나이: str, 성별: str, 경로: str):
    if not any(role.id in [1475269649754230904, 1475271206042337452] for role in interaction.user.roles):
        return await interaction.response.send_message("❌ 권한 없음.", ephemeral=True)
    roles_to_add = [interaction.guild.get_role(BAEKYA_ROLE_ID), interaction.guild.get_role(SEOLYA_ROLE_ID)]
    if 성별 in ["남", "남자"]: roles_to_add.append(interaction.guild.get_role(ROLES_LIST["남자"]))
    elif 성별 in ["여", "여자"]: roles_to_add.append(interaction.guild.get_role(ROLES_LIST["여자"]))
    if ROLES_LIST["age"].get(나이): roles_to_add.append(interaction.guild.get_role(ROLES_LIST["age"][나이]))
    await 유저.edit(nick=f"『 백야 』 {이름}")
    await 유저.add_roles(*[r for r in roles_to_add if r])
    if interaction.guild.get_role(ROLES_LIST["미인증"]) in 유저.roles:
        await 유저.remove_roles(interaction.guild.get_role(ROLES_LIST["미인증"]))
    stats = load_stats(); stats[str(interaction.user.id)] = stats.get(str(interaction.user.id), 0) + 1; save_stats(stats)
    log_embed = discord.Embed(title="❄️ 뉴페기록", color=discord.Color.blue())
    log_embed.add_field(name="대상자", value=유저.mention); log_embed.add_field(name="안내자", value=interaction.user.mention)
    log_embed.add_field(name="정보", value=f"나이: {나이} / 성별: {성별} / 경로: {경로}\n횟수: {stats[str(interaction.user.id)]}회", inline=False)
    await bot.get_channel(log_channel_id).send(embed=log_embed)
    await interaction.response.send_message("✅ 지급 완료.", ephemeral=True)

# 봇 실행
if token:
    bot.run(token)
else:
    print("❌ 에러: DISCORD_TOKEN 환경변수가 설정되지 않았습니다.")
