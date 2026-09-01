# ============================================================
#  Makefile — Hệ thống quản trị tri thức (Stack Overflow Clone)
#  Dùng: make <target>  (xem danh sách: make help)
# ============================================================

# ---------- Cấu hình ----------
BACKEND_DIR   := backend
FRONTEND_DIR  := frontend
VENV          := venv
PYTHON        := venv/bin/python
PIP           := venv/bin/pip
UVICORN       := venv/bin/uvicorn
MONGO_NAME    := mongo
MONGO_PORT    := 27017
BACKEND_PORT  := 8000
FRONTEND_PORT := 5173

# ---------- Màu sắc cho output ----------
GREEN  := \033[0;32m
YELLOW := \033[0;33m
CYAN   := \033[0;36m
RED    := \033[0;31m
NC     := \033[0m

# ---------- Mặc định ----------
.DEFAULT_GOAL := help

# ============================================================
#  CÀI ĐẶT
# ============================================================

## Cài đặt toàn bộ dependencies (backend + frontend)
setup: venv backend-install frontend-install
	@echo "$(GREEN)✅ Setup hoàn tất! Chạy 'make db' rồi 'make seed' để khởi tạo dữ liệu.$(NC)"

## Tạo môi trường ảo Python (nếu chưa có)
venv:
	@if [ ! -d "$(BACKEND_DIR)/$(VENV)" ]; then \
		echo "$(CYAN)⏳ Tạo venv...$(NC)"; \
		cd $(BACKEND_DIR) && python3 -m venv venv; \
	else \
		echo "$(YELLOW)ℹ️  venv đã tồn tại, bỏ qua.$(NC)"; \
	fi

## Cài dependencies backend
backend-install:
	@echo "$(CYAN)⏳ Cài dependencies backend...$(NC)"
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Backend dependencies đã cài.$(NC)"

## Cài dependencies frontend
frontend-install:
	@echo "$(CYAN)⏳ Cài dependencies frontend...$(NC)"
	cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)✅ Frontend dependencies đã cài.$(NC)"

## Tạo file .env cho backend (nếu chưa có)
env:
	@if [ ! -f $(BACKEND_DIR)/.env ]; then \
		echo "$(CYAN)⏳ Tạo backend/.env...$(NC)"; \
		cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env 2>/dev/null || \
		printf 'MONGO_URI=mongodb://localhost:27017\nMONGO_DB_NAME=knowledge_hub\nJWT_SECRET=doi-chuoi-bi-mat-nay-thanh-gia-tri-rieng-cua-ban\nJWT_EXPIRES_MINUTES=10080\nPORT=8000\nSEARCH_TOP_K_DEFAULT=10\n' > $(BACKEND_DIR)/.env; \
	else \
		echo "$(YELLOW)ℹ️  backend/.env đã tồn tại, bỏ qua.$(NC)"; \
	fi
	@if [ ! -f $(FRONTEND_DIR)/.env ]; then \
		echo "$(CYAN)⏳ Tạo frontend/.env...$(NC)"; \
		cp $(FRONTEND_DIR)/.env.example $(FRONTEND_DIR)/.env 2>/dev/null || \
		printf 'VITE_API_BASE_URL=http://localhost:8000\n' > $(FRONTEND_DIR)/.env; \
	else \
		echo "$(YELLOW)ℹ️  frontend/.env đã tồn tại, bỏ qua.$(NC)"; \
	fi

# ============================================================
#  MONGODB
# ============================================================

## Khởi động MongoDB (Hỗ trợ cả Service hệ thống & Docker)
db:
	@if nc -z localhost 27017 2>/dev/null || pgrep -x mongod >/dev/null 2>&1; then \
		echo "$(GREEN)✅ MongoDB đang chạy tại localhost:27017 (System Service).$(NC)"; \
	elif command -v docker >/dev/null 2>&1; then \
		if docker ps --format '{{.Names}}' | grep -q '^$(MONGO_NAME)$$'; then \
			echo "$(GREEN)✅ MongoDB đang chạy (Docker container '$(MONGO_NAME)').$(NC)"; \
		elif docker ps -a --format '{{.Names}}' | grep -q '^$(MONGO_NAME)$$'; then \
			echo "$(YELLOW)⏳ Khởi động lại container '$(MONGO_NAME)'...$(NC)"; \
			docker start $(MONGO_NAME); \
		else \
			echo "$(CYAN)⏳ Tạo container MongoDB...$(NC)"; \
			docker run -d -p $(MONGO_PORT):$(MONGO_PORT) --name $(MONGO_NAME) mongo:7; \
		fi \
	elif command -v systemctl >/dev/null 2>&1; then \
		echo "$(CYAN)⏳ Thử khởi động service mongod...$(NC)"; \
		sudo systemctl start mongod || sudo service mongodb start; \
	else \
		echo "$(RED)❌ Không tìm thấy MongoDB đang chạy và không có Docker.$(NC)"; \
		exit 1; \
	fi

## Dừng MongoDB
db-stop:
	@if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q '^$(MONGO_NAME)$$'; then \
		echo "$(YELLOW)⏳ Dừng MongoDB container...$(NC)"; \
		docker stop $(MONGO_NAME); \
	elif command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet mongod; then \
		echo "$(YELLOW)⏳ Dừng service mongod...$(NC)"; \
		sudo systemctl stop mongod; \
	else \
		echo "$(YELLOW)ℹ️  MongoDB không đang chạy.$(NC)"; \
	fi

## Xóa container MongoDB (kèm dữ liệu)
db-rm:
	@if command -v docker >/dev/null 2>&1; then \
		docker rm -f $(MONGO_NAME) 2>/dev/null || echo "$(YELLOW)ℹ️  Không có container '$(MONGO_NAME)'.$(NC)"; \
	fi

# ============================================================
#  SEED DỮ LIỆU
# ============================================================

## Seed dữ liệu: tài khoản test + 400 câu hỏi mẫu
seed: env
	@echo "$(CYAN)⏳ Seed tài khoản test...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m app.seed
	@echo "$(CYAN)⏳ Seed 400 câu hỏi mẫu...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m app.seed_questions
	@echo "$(GREEN)✅ Seed hoàn tất! Mật khẩu chung: Test@123$(NC)"

## Seed số lượng lớn câu hỏi độc nhất (Ví dụ: make seed-massive COUNT=100000)
COUNT ?= 10000
seed-massive: env
	@echo "$(CYAN)⏳ Seed $(COUNT) câu hỏi độc nhất (100% không trùng lặp)...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m app.seed_massive_questions --count $(COUNT)
	@echo "$(GREEN)✅ Seed quy mô lớn hoàn tất!$(NC)"

# ============================================================
#  CHẠY SERVER
# ============================================================

## Chạy backend (cổng 8000)
backend: ## Chạy backend server
	@echo "$(GREEN)🚀 Backend chạy tại http://localhost:$(BACKEND_PORT)/docs$(NC)"
	cd $(BACKEND_DIR) && $(UVICORN) app.main:app --reload --port $(BACKEND_PORT)

## Chạy frontend (cổng 5173)
frontend: ## Chạy frontend dev server
	@echo "$(GREEN)🚀 Frontend chạy tại http://localhost:$(FRONTEND_PORT)$(NC)"
	cd $(FRONTEND_DIR) && npm run dev

## Chạy cả backend + frontend cùng lúc (Ctrl+C để dừng)
dev: ## Chạy cả backend và frontend (chế độ localhost)
	@echo "$(GREEN)🚀 Khởi động backend + frontend (localhost)...$(NC)"
	@trap 'kill 0' INT TERM; \
	( cd $(BACKEND_DIR) && $(UVICORN) app.main:app --reload --port $(BACKEND_PORT) ) & \
	( cd $(FRONTEND_DIR) && npm run dev ) & \
	wait

## Chạy backend + frontend ở chế độ mở LAN (cho máy khác trong mạng WiFi truy cập)
lan: ## Chạy hệ thống cho mạng LAN/WiFi truy cập
	@echo "$(GREEN)🌐 Khởi động ở chế độ LAN (host 0.0.0.0)...$(NC)"
	@trap 'kill 0' INT TERM; \
	( cd $(BACKEND_DIR) && $(UVICORN) app.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT) ) & \
	( cd $(FRONTEND_DIR) && npx vite --host 0.0.0.0 ) & \
	wait

## Mở Tunnel chia sẻ link HTTPS công khai cho người ở xa qua Internet (không cần deploy)
tunnel: ## Tạo link HTTPS công khai cho người ở xa
	@echo "$(CYAN)🌐 Đang tạo đường link HTTPS công khai bằng Cloudflare Tunnel (HTTP/2)...$(NC)"
	npx -y cloudflared tunnel --protocol http2 --url http://localhost:$(FRONTEND_PORT)

# ============================================================
#  KIỂM THỬ & TIỆN ÍCH
# ============================================================

## Chạy bộ test end-to-end (không cần MongoDB thật)
test: ## Chạy test end-to-end
	@echo "$(CYAN)⏳ Cài thư viện test (nếu thiếu)...$(NC)"
	cd $(BACKEND_DIR) && $(PIP) install mongomock mongomock-motor httpx2 -q
	@echo "$(CYAN)⏳ Chạy test end-to-end...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m app.dev_e2e_test

## Chạy benchmark TF-IDF (cần MongoDB thật + đã seed)
benchmark: ## Chạy benchmark TF-IDF
	@echo "$(CYAN)⏳ Chạy benchmark TF-IDF...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m app.benchmark_search

## Reindex toàn bộ dữ liệu tìm kiếm (cần backend đang chạy)
reindex: ## Reindex toàn bộ chỉ mục TF-IDF
	@echo "$(CYAN)⏳ Lấy token admin...$(NC)"
	@TOKEN=$$(curl -s -X POST http://localhost:$(BACKEND_PORT)/api/auth/login \
		-H "Content-Type: application/json" \
		-d '{"username":"admin","password":"Test@123"}' | \
		$(PYTHON) -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null); \
	if [ -z "$$TOKEN" ]; then \
		echo "$(RED)❌ Không lấy được token. Đảm bảo backend đang chạy tại cổng $(BACKEND_PORT).$(NC)"; \
		exit 1; \
	fi; \
	echo "$(CYAN)⏳ Reindex...$(NC)"; \
	curl -s -X POST http://localhost:$(BACKEND_PORT)/api/admin/search/reindex \
		-H "Authorization: Bearer $$TOKEN"; \
	echo ""; \
	echo "$(GREEN)✅ Reindex hoàn tất.$(NC)"

## Kiểm tra sức khỏe backend
health: ## Kiểm tra backend có chạy không
	@curl -s http://localhost:$(BACKEND_PORT)/health || echo "$(RED)❌ Backend chưa chạy.$(NC)"

# ============================================================
#  DỌN DẸP
# ============================================================

## Xóa cache Python/Node
clean: ## Dọn cache
	@echo "$(YELLOW)⏳ Dọn cache Python...$(NC)"
	find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(YELLOW)⏳ Dọn cache Node...$(NC)"
	rm -rf $(FRONTEND_DIR)/node_modules/.vite 2>/dev/null || true
	@echo "$(GREEN)✅ Đã dọn cache.$(NC)"

## Xóa hoàn toàn môi trường (venv + node_modules) — cần chạy lại make setup
distclean: clean
	@echo "$(RED)⏳ Xóa venv + node_modules...$(NC)"
	rm -rf $(VENV) $(FRONTEND_DIR)/node_modules
	@echo "$(GREEN)✅ Đã xóa. Chạy 'make setup' để cài lại.$(NC)"

# ============================================================
#  TRỢ GIÚP
# ============================================================

## Hiển thị danh sách lệnh
help:
	@echo "$(CYAN)============================================$(NC)"
	@echo "$(CYAN)  Hệ thống quản trị tri thức — Makefile$(NC)"
	@echo "$(CYAN)============================================$(NC)"
	@echo ""
	@echo "$(GREEN)Cài đặt & Khởi động:$(NC)"
	@echo "  make setup        Cài toàn bộ dependencies (backend + frontend)"
	@echo "  make db           Khởi động MongoDB (Docker)"
	@echo "  make db-stop      Dừng MongoDB"
	@echo "  make seed         Seed dữ liệu (tài khoản + 400 câu hỏi)"
	@echo "  make backend      Chạy backend (http://localhost:8000/docs)"
	@echo "  make frontend     Chạy frontend (http://localhost:5173)"
	@echo "  make dev          Chạy cả backend + frontend"
	@echo ""
	@echo "$(GREEN)Kiểm thử & Tiện ích:$(NC)"
	@echo "  make test         Chạy bộ test end-to-end (42 test)"
	@echo "  make benchmark    Chạy benchmark TF-IDF"
	@echo "  make reindex      Reindex toàn bộ dữ liệu tìm kiếm"
	@echo "  make health       Kiểm tra backend có chạy không"
	@echo ""
	@echo "$(GREEN)Dọn dẹp:$(NC)"
	@echo "  make clean        Dọn cache"
	@echo "  make distclean    Xóa venv + node_modules (cài lại bằng make setup)"
	@echo ""
	@echo "$(GREEN)Ví dụ nhanh:$(NC)"
	@echo "  make setup && make db && make seed && make dev"
	@echo "  → Mở http://localhost:5173 (mật khẩu test: Test@123)"
	@echo ""

# ---------- Đánh dấu các target không phải file ----------
.PHONY: setup venv backend-install frontend-install env \
        db db-stop db-rm seed seed-massive backend frontend dev \
        test benchmark reindex health clean distclean help
