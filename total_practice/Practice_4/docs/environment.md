# Môi trường chạy Practice 4

Notebook chính: `notebooks/practice4.ipynb`

## Môi trường đã cài sẵn

Môi trường `.venv` đã được tạo tại `Practice_4/.venv` và đã cài toàn bộ
dependency trong `requirements.txt`. Kernel đã đăng ký với tên **Practice 4
(.venv, Python 3.12)**.

Khi làm việc hằng ngày, không cần chạy `pip install` lại.

## Tạo lại môi trường khi cần

Chạy từ thư mục `total_practice/Practice_4`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m ipykernel install --prefix .venv \
  --name practice4-venv \
  --display-name "Practice 4 (.venv, Python 3.12)"
```

Thư mục `.venv` là môi trường cục bộ và không được commit. File
`requirements.txt` là nguồn dependency có thể dùng để tái tạo môi trường.

## Chạy notebook trong VS Code

1. Mở riêng thư mục `total_practice/Practice_4` bằng VS Code.
2. Cài/ bật hai extension **Python** và **Jupyter** của Microsoft.
3. Mở `notebooks/practice4.ipynb`.
4. Ở góc phải phía trên notebook, chọn kernel **Practice 4 (.venv, Python 3.12)**.
5. Chạy từng cell hoặc chọn **Run All**.

VS Code sẽ dùng interpreter `.venv/bin/python` nhờ cấu hình tại
`.vscode/settings.json`. Không cần chạy lệnh `jupyter notebook` trong terminal.
