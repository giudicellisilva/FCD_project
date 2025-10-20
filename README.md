# 📊 Projeto - Fundamentos em Ciência de Dados 2025.2

## 🧱 1. Pré-requisitos

Antes de iniciar, verifique se o **Python** está instalado em sua máquina:

```bash
python --version
```

✅ **Versão mínima:** 3.10  
💡 **Recomendado:** 3.12  

Se não estiver instalado, baixe em:  
🔗 [Python](https://www.python.org/downloads/)

Também é necessário ter o **Git** instalado para clonar o repositório:  
🔗 [Git](https://git-scm.com/downloads)

---

## 🚀 2. Instalação e Execução

### 1️⃣ Clone o repositório
```bash
git clone https://github.com/giudicellisilva/FCD_project.git
cd FCD_project
```


---

### 2️⃣ Crie e ative um ambiente virtual

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3️⃣ Instale as dependências
```bash
pip install -r requirements.txt
```

> Se o arquivo `requirements.txt` ainda não existir, crie um com as seguintes dependências:
> ```txt
> streamlit
> pandas
> plotly
> bcrypt
> ```

---

### 4️⃣ Execute o projeto
```bash
streamlit run app.py
```

O sistema abrirá automaticamente no navegador padrão.
---


## 📦 3. Projetos Desenvolvidos

### 🧩 **Projeto 1 – Dashboard de Controle de Estoque**

**Objetivo:**  
Desenvolver um dashboard interativo em Python + Streamlit para monitoramento e análise do estoque de produtos de uma empresa.

**Funcionalidades Implementadas:**
- Exibição de todos os produtos cadastrados com:  
  `ID`, `Nome`, `Categoria`, `Quantidade em estoque`, `Estoque mínimo` e `Preço unitário`.
- Tabela interativa com filtro por categoria.  
- Indicador visual mostrando a quantidade de produtos **abaixo do estoque mínimo**.  
- Gráfico de barras comparando **Estoque Atual vs Estoque Mínimo**, destacando produtos em alerta.  
- Cálculo e exibição do **valor total do estoque**, atualizado dinamicamente conforme os filtros.  

---

## 🧠 4. Decisões Estratégicas Possíveis

Com base nos dados do dashboard, os gestores poderão:
- Identificar produtos com risco de ruptura.  
- Avaliar necessidades de reposição.  
- Planejar o orçamento para reabastecimento.  
- Tomar decisões estratégicas para manter o estoque adequado.  


## 👨‍💻 Autor
**Giudicelli Elias**
📘 Projeto desenvolvido para a disciplina **Fundamentos em Ciência de Dados 2025.2**