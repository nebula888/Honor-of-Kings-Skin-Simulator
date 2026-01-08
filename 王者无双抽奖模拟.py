import tkinter as tk
from tkinter import ttk, messagebox
import random
import secrets

# ================= 默认配置 =================

DEFAULT_MAIN_ITEMS = [
    {"name": "随机限定皮肤礼", "val": 0, "prob": 0.4},
    {"name": "随机传说皮肤", "val": 0, "prob": 0.5},
    {"name": "随机皮肤(史诗/勇者/伴生)", "val": 0, "prob": 13.5},
    {"name": "无相积分", "val": 68, "prob": 0.8},
    {"name": "无相积分", "val": 28, "prob": 4.0},
    {"name": "无相积分", "val": 18, "prob": 23.7},
    {"name": "无相积分", "val": 8, "prob": 30.0},
    {"name": "皮肤碎片x8", "val": 0, "prob": 15.0},
    {"name": "亲密度道具x2", "val": 0, "prob": 12.1}
]

DEFAULT_DECOMP_VALUES = {
    "限定": 288, "天幕": 288, "传说": 120,
    "史诗": 60, "勇者": 40, "伴生": 20,
    "皮肤碎片x8": 5, "亲密度道具x2": 5
}

DEFAULT_LIMITED_POOL = [
    {"name": "孙悟空-无相", "prob": 0.34, "type": "限定"},
    {"name": "瑶-真我赫兹", "prob": 0.33, "type": "限定"},
    {"name": "甄姬-雪境奇遇", "prob": 0.33, "type": "限定"},
    {"name": "雪境奇遇全屏天幕", "prob": 1.0, "type": "天幕"},
    {"name": "小乔-山海·琳琅生", "prob": 32.0, "type": "限定"},
    {"name": "赵云-龙胆", "prob": 33.0, "type": "限定"},
    {"name": "妲己-热情桑巴", "prob": 33.0, "type": "限定"}
]

DEFAULT_QUALITY_RATIOS = {"史诗": 10.0, "勇者": 30.0, "伴生": 60.0}

# ================= 核心逻辑类 =================

class GachaLogic:
    def __init__(self):
        self.secure_rng = random.SystemRandom()
        self.reset_data()

    def reset_data(self):
        self.points = 0
        self.total_draws = 0
        self.round_draws = 0
        self.owned_skins = set()
        self.wish_box = []
        self.item_counter = 0

    def get_value_from_config(self, item_type, item_name, config):
        table = config['decomp_table']
        if item_name in table: return table[item_name]
        if item_type in table: return table[item_type]
        return 5

    def draw_one(self, config):
        if not config['main_items']:
            return {"type": "error", "msg": "错误：主奖池为空！请在【主概率】中添加奖励。", "color": "red"}

        self.total_draws += 1
        self.round_draws += 1
        
        # 1. 抽取
        items = config['main_items']
        weights = [item['prob'] for item in items]
        chosen_obj = self.secure_rng.choices(items, weights=weights, k=1)[0]
        
        name = chosen_obj['name']
        val = chosen_obj['val']
        
        result_item = None 

        # 2. 逻辑分支 (基于名称关键字)
        
        # A. 纯积分 (Value > 0)
        if val > 0:
            self.points += val
            return {
                "type": "points", 
                "msg": f"获得 {name} (获得无相积分: {val}个)", 
                "color": "blue"
            }
            
        # B. 特殊关键字：限定池
        elif name == "随机限定皮肤礼":
            l_items = config['limited_pool']
            if l_items:
                l_weights = [x['prob'] for x in l_items]
                idx = self.secure_rng.choices(range(len(l_items)), weights=l_weights, k=1)[0]
                chosen = l_items[idx]
                result_item = {"name": chosen['name'], "type": chosen['type'], "display_type": "限定"}
            else:
                result_item = {"name": "限定池为空", "type": "错误", "display_type": "normal"}

        # C. 特殊关键字：传说皮肤
        elif name == "随机传说皮肤":
            result_item = {"name": "随机传说皮肤", "type": "传说", "display_type": "传说"}
            
        # D. 特殊关键字：随机皮肤 (匹配包含关系)
        elif "随机皮肤" in name:
            q_ratios = config['quality_ratios']
            q_keys = list(q_ratios.keys())
            q_weights = list(q_ratios.values())
            quality = self.secure_rng.choices(q_keys, weights=q_weights, k=1)[0]
            result_item = {"name": f"随机{quality}皮肤", "type": quality, "display_type": quality}
            
        # E. 普通道具/自定义物品
        else:
            result_item = {"name": name, "type": "道具", "display_type": "道具"}

        # 3. 物品处理
        if result_item:
            c_map = {"传说": "gold", "史诗": "purple", "勇者": "green", "限定": "red", "天幕": "red"}
            color_tag = c_map.get(result_item.get('display_type', ''), "normal")
            if result_item['type'] == "伴生": color_tag = "normal"

            decomp_val = self.get_value_from_config(result_item['type'], result_item['name'], config)

            is_duplicate = False
            if ("限定" in result_item.get('display_type', '') or "天幕" in result_item['name']):
                if result_item['name'] in self.owned_skins:
                    is_duplicate = True
            
            if is_duplicate:
                self.points += decomp_val
                return {
                    "type": "converted", 
                    "msg": f"抽到已拥有【{result_item['name']}】，转化无相积分: {decomp_val}个", 
                    "color": "purple"
                }
            else:
                self.item_counter += 1
                self.wish_box.append({
                    "id": self.item_counter,
                    "name": result_item['name'],
                    "type": result_item['type'],
                    "decompose_val": decomp_val
                })
                return {"type": "box", "msg": f"获得【{result_item['name']}】，已存入祈愿盒", "color": color_tag}

    def check_milestones(self, rules, config):
        msgs = []
        if self.total_draws > rules['total_max']: return msgs

        # 宝箱节点
        if self.round_draws in rules['box_counts']:
            msgs.append({
                "msg": f"[保底] 【累抽{self.round_draws}发】随机皮肤宝箱",
                "color": "green"
            })
            
            q_ratios = config['quality_ratios']
            q_keys = list(q_ratios.keys())
            q_weights = list(q_ratios.values())
            quality = self.secure_rng.choices(q_keys, weights=q_weights, k=1)[0]
            
            name = f"随机{quality}皮肤(累抽赠送)"
            val = self.get_value_from_config(quality, name, config)

            self.item_counter += 1
            self.wish_box.append({
                "id": self.item_counter,
                "name": name,
                "type": quality,
                "decompose_val": val
            })
            
            color_map = {"史诗": "purple", "勇者": "green", "伴生": "normal"}
            msgs.append({
                "msg": f"   └─ 开启获得: {name}",
                "color": color_map.get(quality, "normal")
            })

        # 大奖节点
        if self.round_draws >= rules['round_max']:
            pts = rules['round_points']
            self.points += pts
            msgs.append({"msg": f"【累抽{self.round_draws}发大奖】获得无相积分: {pts}个", "color": "red"})
            self.round_draws = 0 
            msgs.append({"msg": "--- 累抽轮次已重置 ---", "color": "normal"})

        return msgs

# ================= 图形界面类 =================

class GachaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("王者荣耀无双祈愿模拟器 v7.0")
        self.root.geometry("1280x900")
        self.logic = GachaLogic()
        self.setup_styles()
        self.create_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Bold.TLabel", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Title.TLabel", font=("Microsoft YaHei", 12, "bold"), foreground="#333")
        style.configure("Del.TButton", foreground="red")
        style.configure("Help.TButton", foreground="blue", font=("Microsoft YaHei", 9, "bold"))

    def create_ui(self):
        # 顶部工具栏
        top_frame = ttk.Frame(self.root, padding=5)
        top_frame.pack(fill=tk.X)
        
        # 按钮
        ttk.Button(top_frame, text="⚠ 全局重置", command=self.reset_all).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="? 帮助 / 规则说明", style="Help.TButton", command=self.show_help_window).pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(top_frame, text="无双祈愿系统 v7.0", style="Title.TLabel").pack(side=tk.LEFT, padx=10)

        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.settings_frame = ttk.Frame(main_paned, width=450)
        self.notebook = ttk.Notebook(self.settings_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_main_probs = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_main_probs, text="主概率(可增删)")
        self.init_main_probs_tab()

        self.tab_limited = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_limited, text="限定池")
        self.init_limited_tab()
        
        self.tab_decomp = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_decomp, text="分解/转化设置")
        self.init_decomp_tab()

        self.tab_rules = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_rules, text="累抽规则")
        self.init_rules_tab()

        main_paned.add(self.settings_frame, weight=1)

        self.game_frame = ttk.Frame(main_paned)
        main_paned.add(self.game_frame, weight=3)
        self.init_game_ui()

    # --- 帮助窗口 ---
    def show_help_window(self):
        help_win = tk.Toplevel(self.root)
        help_win.title("关键词与逻辑说明")
        help_win.geometry("600x500")
        
        txt = tk.Text(help_win, wrap=tk.WORD, font=("Microsoft YaHei", 10), padx=10, pady=10, bg="#f5f5f5")
        txt.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scroll = ttk.Scrollbar(txt, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 设置Tag样式
        txt.tag_config("title", font=("Microsoft YaHei", 12, "bold"), foreground="black")
        txt.tag_config("keyword", font=("Microsoft YaHei", 10, "bold"), foreground="red", background="#ffe6e6")
        txt.tag_config("normal", foreground="#333")
        txt.tag_config("warn", foreground="red")

        content = [
            ("特别注意：系统核心关键词", "title"),
            ("\n本系统通过【奖励名称】来识别特殊逻辑。如果您修改了以下名称，会导致对应的特殊功能失效（变为普通物品）。\n", "normal"),
            
            ("\n1. 随机限定皮肤礼", "keyword"),
            ("\n   - 对应功能：触发【限定池】抽奖。", "normal"),
            ("\n   - 警告：如果改名，系统将无法关联到“限定池”标签页中的奖励，只会给用户一个名字叫新名字的普通道具。", "warn"),
            
            ("\n2. 随机传说皮肤", "keyword"),
            ("\n   - 对应功能：系统识别为传说品质，显示为金色，且分解价值按照传说皮肤计算。", "normal"),
            
            ("\n3. 随机皮肤 (或包含此文字)", "keyword"),
            ("\n   - 对应功能：触发【内部随机品质分布】逻辑（即根据10%/30%/60%概率出史诗/勇者/伴生）。", "normal"),
            ("\n   - 警告：如果改为“普通皮肤礼包”，将不再根据品质概率产出，而是直接获得该物品。", "warn"),
            
            ("\n4. 积分逻辑 (Value > 0)", "keyword"),
            ("\n   - 对应功能：只要在“积分”输入框中填写的数字大于0，该奖励就会自动被视为【无相积分】。", "normal"),
            ("\n   - 说明：名称可以随意修改（如“大额积分包”），只要积分值>0，系统会自动处理。", "normal"),
            
            ("\n\n常见错误指南：", "title"),
            ("\nQ: 为什么我把“随机限定皮肤礼”改名为“限定大礼包”后，抽不到孙悟空了？", "normal"),
            ("\nA: 因为系统不再识别它是限定礼的入口，它现在只是一个普通的物品。请改回原名。", "warn"),
            
            ("\nQ: 我删除了所有奖励会怎样？", "normal"),
            ("\nA: 系统会弹窗警告“主奖池为空”，阻止抽奖以防止崩溃。", "normal")
        ]
        
        for text, tag in content:
            txt.insert(tk.END, text, tag)
            
        txt.config(state='disabled') # 禁止编辑

    # --- 主界面逻辑保持不变 ---
    def init_main_probs_tab(self):
        header_frame = ttk.Frame(self.tab_main_probs)
        header_frame.pack(fill=tk.X, pady=2)
        ttk.Label(header_frame, text="名称 (保留关键字见帮助)", width=22).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="积分(0为物品)", width=12).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="概率%", width=6).pack(side=tk.LEFT)
        
        canvas = tk.Canvas(self.tab_main_probs, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_main_probs, orient="vertical", command=canvas.yview)
        self.main_scroll_frame = ttk.Frame(canvas)
        
        self.main_scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.main_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y", in_=canvas)

        ctrl_frame = ttk.Frame(self.tab_main_probs, padding=5)
        ctrl_frame.pack(side="bottom", fill=tk.X)
        ttk.Button(ctrl_frame, text="+ 添加新奖励类", command=self.add_new_main_row).pack(fill=tk.X)
        
        self.main_row_widgets = []
        for item in DEFAULT_MAIN_ITEMS:
            self.create_main_row(item['name'], item['val'], item['prob'])

        ttk.Separator(self.tab_main_probs, orient='horizontal').pack(fill='x', pady=5)
        ttk.Label(self.tab_main_probs, text="内部随机品质分布 (%)", style="Bold.TLabel").pack(pady=2)
        self.quality_vars = {}
        q_frame = ttk.Frame(self.tab_main_probs)
        q_frame.pack(fill=tk.X)
        for k, v in DEFAULT_QUALITY_RATIOS.items():
            f = ttk.Frame(q_frame)
            f.pack(fill=tk.X)
            ttk.Label(f, text=k, width=10).pack(side=tk.LEFT)
            var = tk.DoubleVar(value=v)
            self.quality_vars[k] = var
            ttk.Entry(f, textvariable=var, width=6).pack(side=tk.RIGHT)

    def create_main_row(self, name_val, point_val, prob_val):
        row_frame = ttk.Frame(self.main_scroll_frame)
        row_frame.pack(fill=tk.X, pady=2)
        var_name = tk.StringVar(value=name_val)
        var_point = tk.IntVar(value=point_val)
        var_prob = tk.DoubleVar(value=prob_val)
        
        e_name = ttk.Entry(row_frame, textvariable=var_name, width=18)
        e_name.pack(side=tk.LEFT, padx=2)
        e_point = ttk.Entry(row_frame, textvariable=var_point, width=8)
        e_point.pack(side=tk.LEFT, padx=2)
        e_prob = ttk.Entry(row_frame, textvariable=var_prob, width=6)
        e_prob.pack(side=tk.LEFT, padx=2)
        
        btn_del = ttk.Button(row_frame, text="×", width=3, style="Del.TButton",
                             command=lambda: self.delete_main_row(row_frame))
        btn_del.pack(side=tk.LEFT, padx=5)
        
        self.main_row_widgets.append({
            "frame": row_frame,
            "vars": {"name": var_name, "point": var_point, "prob": var_prob}
        })

    def add_new_main_row(self):
        self.create_main_row("新奖励", 0, 0.0)

    def delete_main_row(self, frame_obj):
        frame_obj.destroy()
        self.main_row_widgets = [row for row in self.main_row_widgets if row['frame'] != frame_obj]

    def init_limited_tab(self):
        ttk.Label(self.tab_limited, text="限定池内容", foreground="gray").pack()
        canvas = tk.Canvas(self.tab_limited)
        scrollbar = ttk.Scrollbar(self.tab_limited, orient="vertical", command=canvas.yview)
        self.limited_scroll_frame = ttk.Frame(canvas)
        self.limited_scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.limited_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.limited_vars = []
        for item in DEFAULT_LIMITED_POOL:
            self.add_limited_row(item['name'], item['prob'])

    def add_limited_row(self, name, prob):
        f = ttk.Frame(self.limited_scroll_frame)
        f.pack(fill=tk.X, pady=2)
        n_var = tk.StringVar(value=name)
        p_var = tk.DoubleVar(value=prob)
        ttk.Entry(f, textvariable=n_var, width=18).pack(side=tk.LEFT)
        ttk.Entry(f, textvariable=p_var, width=6).pack(side=tk.LEFT)
        self.limited_vars.append({"name": n_var, "prob": p_var})

    def init_decomp_tab(self):
        self.decomp_vars = {}
        for k, v in DEFAULT_DECOMP_VALUES.items():
            f = ttk.Frame(self.tab_decomp)
            f.pack(fill=tk.X, pady=4)
            ttk.Label(f, text=k, width=15).pack(side=tk.LEFT)
            var = tk.IntVar(value=v)
            self.decomp_vars[k] = var
            ttk.Entry(f, textvariable=var, width=8).pack(side=tk.RIGHT)

    def init_rules_tab(self):
        self.rule_vars = {}
        def create_entry(label, default_val, key):
            f = ttk.Frame(self.tab_rules)
            f.pack(fill=tk.X, pady=5)
            ttk.Label(f, text=label).pack(anchor="w")
            var = tk.StringVar(value=str(default_val))
            self.rule_vars[key] = var
            ttk.Entry(f, textvariable=var).pack(fill=tk.X)
        create_entry("宝箱触发节点", "5,10,25", "box_counts")
        create_entry("大奖/重置节点", "40", "round_max")
        create_entry("大奖积分", "288", "round_points")
        create_entry("总抽数上限", "120", "total_max")

    def init_game_ui(self):
        info_panel = ttk.Frame(self.game_frame, padding=10, relief="groove")
        info_panel.pack(fill=tk.X, pady=5)
        self.lbl_total_draws = ttk.Label(info_panel, text="总抽数: 0", font=("Arial", 12))
        self.lbl_total_draws.pack(side=tk.LEFT, padx=10)
        self.lbl_round_draws = ttk.Label(info_panel, text="当前轮进度: 0/40", font=("Arial", 12), foreground="blue")
        self.lbl_round_draws.pack(side=tk.LEFT, padx=10)
        self.lbl_points = ttk.Label(info_panel, text="无相积分: 0", font=("Arial", 14, "bold"), foreground="#FF8C00")
        self.lbl_points.pack(side=tk.RIGHT, padx=10)
        self.log_text = tk.Text(self.game_frame, height=20, state='disabled', bg="#2b2b2b", fg="white", font=("Microsoft YaHei", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5)
        self.log_text.tag_config("gold", foreground="#FFD700", font=("Microsoft YaHei", 10, "bold"))
        self.log_text.tag_config("purple", foreground="#DA70D6")
        self.log_text.tag_config("green", foreground="#00FF7F")
        self.log_text.tag_config("red", foreground="#FF4500", font=("Microsoft YaHei", 10, "bold"))
        self.log_text.tag_config("blue", foreground="#1E90FF")
        self.log_text.tag_config("normal", foreground="white")
        btn_frame = ttk.Frame(self.game_frame, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="单抽 (10币)", command=lambda: self.do_gacha(1)).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="十连 (100币)", command=lambda: self.do_gacha(10)).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        box_frame = ttk.LabelFrame(self.game_frame, text="祈愿盒", padding=5)
        box_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.box_list = tk.Listbox(box_frame, height=8, selectmode=tk.EXTENDED, font=("Consolas", 9))
        self.box_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        box_ctrl = ttk.Frame(box_frame)
        box_ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        ttk.Button(box_ctrl, text="领取", width=8, command=self.claim_item).pack(pady=2)
        ttk.Button(box_ctrl, text="分解", width=8, command=self.decompose_item).pack(pady=2)

    def get_config_snapshot(self):
        main_items = []
        for row in self.main_row_widgets:
            try:
                main_items.append({
                    "name": row['vars']['name'].get(),
                    "val": row['vars']['point'].get(),
                    "prob": row['vars']['prob'].get()
                })
            except ValueError:
                pass
        limited_pool = []
        for item in self.limited_vars:
            limited_pool.append({
                "name": item['name'].get(),
                "prob": item['prob'].get(),
                "type": "限定" if "天幕" not in item['name'].get() else "天幕"
            })
        decomp_table = {k: v.get() for k, v in self.decomp_vars.items()}
        quality_ratios = {k: v.get() for k, v in self.quality_vars.items()}
        try:
            box_counts = [int(x) for x in self.rule_vars['box_counts'].get().split(',')]
        except:
            box_counts = [5, 10, 25]
        rules = {
            "box_counts": box_counts,
            "round_max": int(self.rule_vars['round_max'].get()),
            "round_points": int(self.rule_vars['round_points'].get()),
            "total_max": int(self.rule_vars['total_max'].get())
        }
        return {
            "main_items": main_items,
            "limited_pool": limited_pool, 
            "quality_ratios": quality_ratios, 
            "decomp_table": decomp_table,
            "rules": rules
        }

    def reset_all(self):
        if messagebox.askyesno("确认", "确定要清空所有数据重新开始吗？"):
            self.logic.reset_data()
            self.log_text.config(state='normal')
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state='disabled')
            self.update_ui_display()

    def do_gacha(self, count):
        try:
            config = self.get_config_snapshot()
        except Exception as e:
            messagebox.showerror("配置错误", f"数据读取失败: {e}")
            return

        if not config['main_items']:
            messagebox.showwarning("奖池为空", "当前主奖池没有任何奖励！\n请在【主概率】标签页中添加奖励条目。")
            return

        self.log_to_ui(f"--- 开始 {count} 连抽 ---", "normal")
        for _ in range(count):
            res = self.logic.draw_one(config)
            if res.get('type') == 'error':
                self.log_to_ui(res['msg'], res['color'])
                break
            self.log_to_ui(res['msg'], res['color'])
            
            ms_msgs = self.logic.check_milestones(config['rules'], config)
            for m in ms_msgs:
                self.log_to_ui(m['msg'], m['color'])
        self.update_ui_display()

    def log_to_ui(self, msg, tag):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, msg + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def update_ui_display(self):
        self.lbl_total_draws.config(text=f"总抽数: {self.logic.total_draws}")
        r_max = self.rule_vars['round_max'].get()
        self.lbl_round_draws.config(text=f"当前轮进度: {self.logic.round_draws}/{r_max}")
        self.lbl_points.config(text=f"无相积分: {self.logic.points}")
        self.box_list.delete(0, tk.END)
        for item in self.logic.wish_box:
            self.box_list.insert(tk.END, f"{item['name']} [分:{item['decompose_val']}]")

    def claim_item(self):
        indices = self.box_list.curselection()
        if not indices: return
        for idx in reversed(indices):
            item = self.logic.wish_box.pop(idx)
            if "限定" in item['name'] or "天幕" in item['name']:
                self.logic.owned_skins.add(item['name'])
            self.log_to_ui(f"领取了 {item['name']}", "normal")
        self.update_ui_display()

    def decompose_item(self):
        indices = self.box_list.curselection()
        if not indices: return
        pts = 0
        for idx in reversed(indices):
            item = self.logic.wish_box.pop(idx)
            pts += item['decompose_val']
        self.logic.points += pts
        self.log_to_ui(f"分解获得 {pts} 积分", "blue")
        self.update_ui_display()

if __name__ == "__main__":
    root = tk.Tk()
    app = GachaApp(root)
    root.mainloop()