import re
import os
import uuid
import utils
import PyPDF2
import base64
import hashlib
import conexaoDB
import integradorE2DOC
from tkinter import messagebox


def executar_automacao(arquivos_comprovante):
    tipo_pag_incorreto = []
    modelos_enviados = []
    compv_nao_env = []
    cpfs_errados = []
    relatorio = []

    cliente = integradorE2DOC.E2DocClient()

    if cliente.autenticar() == "Conexão não estabelecida entre os sistemas":
        erro = "Conexão não estabelecida com o E2DOC."
        messagebox.showerror("Erro!", erro)
        raise Exception(erro)

    data_formatada, _ = utils.retornar_data()

    for caminho in arquivos_comprovante:
        banco = utils.retornar_banco(caminho)

        diretorios_primordiais = re.split(r'Financeiro - COMPROVANTES - DESMEMBRAR', caminho)[0]
        data_de_pagamento = re.search(r"\b\d{2}-\d{2}\b", caminho).group()
        competencia = re.search(r"\b\d{4}/\d{2}\b", caminho).group()
        mes_vigente = utils.retornar_mes(competencia.split("/")[1])
        ano_vigente = competencia.split("/")[0]
        competencia = competencia.split("/")[1] + "/" + competencia.split("/")[0]


        with open(caminho, 'rb') as file:

            reader = PyPDF2.PdfReader(file)
            
            num_pages = len(reader.pages)
            
            for page_num in range(num_pages):
                
                page = reader.pages[page_num]
                writer = PyPDF2.PdfWriter()
                writer.add_page(page)
                texto = page.extract_text().replace(" ", "").upper()
                try:
                    chave_comp = re.search(r"CHAVE\d{11}[A-Z0-9]{3}", texto).group()
                except AttributeError:
                    continue

                tipo_pagamento = chave_comp[-3:]
                if tipo_pagamento in ['VAR', 'VAT']:
                    chave_comp = re.search(r"CHAVE\d{11}[A-Z0-9]{3}[A-Za-z0-9]{6}", texto).group()
                    pedido = chave_comp[-6:]

                cpf = chave_comp[5:16]
                try:
                    regiao, centro_de_custo, nome = conexaoDB.consultar_db(cpf)
                except:
                    messagebox.showerror("Erro!", "Não foi possivel se conectar ao banco de dados da empresa.")
                    raise Exception("Não foi possivel se conectar ao banco de dados da empresa.")
                
                if regiao == False:
                    cpfs_errados.append(cpf)

                nome_arquivo = nome + ".pdf"
                if banco == "SANTANDER":
                    nome_arquivo = nome + " - OP DISPONIVEL.pdf"

                if tipo_pagamento == "131" and mes_vigente != "11 - NOVEMBRO":
                    tipo_pagamento == "13A"
                
                if tipo_pagamento == "132" and mes_vigente != "12 - DEZEMBRO":
                    tipo_pagamento == "13A"


                match tipo_pagamento:
                    case 'LOC':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante Frota/LOCAÇÃO VEICULO/MANUAL"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento)   
                        modelo_de_documento = 'LOCAÇÃO'
                        
                    case 'VAT':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante Beneficios/VALE TRANSPORTES"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento, tipo='VT', pedido=pedido)   
                        modelo_de_documento = 'VT'

                    case 'VAR':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante Beneficios/VALE ALIMENTACAO"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento, tipo='VA', pedido=pedido)
                        modelo_de_documento = 'VA'

                    case 'FOL':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante DP/PROVENTOS/PAGTOS MANUAIS"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento, tipo="FOLHA GERAL")
                        modelo_de_documento = 'PROVENTOS'

                    case 'ARV':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante DP/PROVENTOS/PAGTOS MANUAIS"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento, tipo="ADTO REVAP")
                        modelo_de_documento = 'PROVENTOS'

                    case 'ARP':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante DP/PROVENTOS/PAGTOS MANUAIS"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento, tipo="ADTO REPAR")
                        modelo_de_documento = 'PROVENTOS'
                    
                    case '13A':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante DP/13 SALARIO"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento, tipo='13 SALARIO')
                        modelo_de_documento = '13 SALARIO'

                    case '131':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante DP/13 SALARIO"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento, tipo='1ª 13 SALARIO')
                        modelo_de_documento = '13 SALARIO'

                    case '132':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante DP/13 SALARIO"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento, tipo='2ª 13 SALARIO')
                        modelo_de_documento = '13 SALARIO'
                    
                    case '13T':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante DP/13 SALARIO"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento, tipo='TJ 13 SALARIO')
                        modelo_de_documento = '13 SALARIO'
                    
                    case 'RES':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante DP/RESCISOES"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento)
                        modelo_de_documento = 'RESCISÕES'

                    case 'FER':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante DP/FERIAS"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento)
                        modelo_de_documento = 'FÉRIAS'

                    case 'FGT':
                        diretorio_destino = fr"{diretorios_primordiais}Comprovantes - Comprovante DP/MULTA FGTS"
                        diretorio_destino = utils.criar_arvore_diretorios(diretorio_destino, ano_vigente, mes_vigente, data_de_pagamento)
                        modelo_de_documento = 'MULTAS DE FGTS RESCISÓRIA'

                    case _:
                        tipo_pag_incorreto.append(chave_comp)


                caminho_arq = os.path.join(diretorio_destino, nome_arquivo)
                

                if chave_comp not in tipo_pag_incorreto and cpf not in cpfs_errados:
                    with open(caminho_arq, 'wb') as arq_saida:
                        writer.write(arq_saida)

                    tamanho = os.path.getsize(caminho_arq)
                    with open(caminho_arq, 'rb') as arquivo:
                        conteudo = arquivo.read()
                        conteudo_base64 = base64.b64encode(conteudo).decode("utf-8")
                        hash_md5 = hashlib.md5(conteudo).hexdigest().upper()
                    protocolo = str(uuid.uuid4())
                    file_name = protocolo + "_1_0.pdf"

                    match tipo_pagamento:
                        case 'FOL':
                            competencia_folha = int(competencia.split("/")[0])
                            if competencia_folha == 1:
                                ano = int(competencia.split("/")[1]) - 1
                                competencia_folha = "12/" + str(ano)
                            else:
                                competencia_folha -= 1
                                competencia_folha = f"{competencia_folha:02}" + "/" + competencia.split("/")[1]
                            try:
                                cliente.iniciar_sincronismo(protocolo, competencia_folha, cpf, nome, banco, regiao, centro_de_custo)
                                cliente.enviar_partes_do_arquivo(file_name, conteudo_base64)
                                cliente.efetivar_envio(modelo_de_documento, data_formatada, hash_md5, tamanho)
                                cliente.finalizar_envio()
                            except Exception as e:
                                compv_nao_env.append([nome, modelo_de_documento, chave_comp, e])
                        
                        case 'LOC':
                            try:
                                cliente.iniciar_sincronismo(protocolo, competencia, cpf, nome, banco, regiao, centro_de_custo, modelo_de_pasta='FINANCEIRO - FROTA', label='Diferente')
                                cliente.enviar_partes_do_arquivo(file_name, conteudo_base64)
                                cliente.efetivar_envio(modelo_de_documento, data_formatada, hash_md5, tamanho, modelo_de_pasta='FINANCEIRO - FROTA')
                                cliente.finalizar_envio()
                            except Exception as e:
                                compv_nao_env.append([nome, modelo_de_documento, chave_comp, e])
                        
                        case 'VAR' | 'VAT':
                            try:
                                cliente.iniciar_sincronismo(protocolo, competencia, cpf, nome, banco, regiao, centro_de_custo, modelo_de_pasta='FINANCEIRO - BENEFICIOS', label='Diferente', pedido=pedido)
                                cliente.enviar_partes_do_arquivo(file_name, conteudo_base64)
                                cliente.efetivar_envio(modelo_de_documento, data_formatada, hash_md5, tamanho, modelo_de_pasta='FINANCEIRO - BENEFICIOS')
                                cliente.finalizar_envio()
                            except Exception as e:
                                compv_nao_env.append([nome, modelo_de_documento, chave_comp, e])
                            
                        case _:
                            try:
                                cliente.iniciar_sincronismo(protocolo, competencia, cpf, nome, banco, regiao, centro_de_custo)
                                cliente.enviar_partes_do_arquivo(file_name, conteudo_base64)
                                cliente.efetivar_envio(modelo_de_documento, data_formatada, hash_md5, tamanho)
                                cliente.finalizar_envio()
                            except Exception as e:
                                compv_nao_env.append([nome, modelo_de_documento, chave_comp, e])


                    if chave_comp not in compv_nao_env:
                        if tipo_pagamento == 'FOL':
                            relatorio.append([nome, "  -  ", modelo_de_documento, "  -  ", competencia_folha])
                        else:
                            relatorio.append([nome, "  -  ", modelo_de_documento, "  -  ", competencia])
                        modelos_enviados.append(modelo_de_documento)
                                

    utils.enviar_email(relatorio, tipo_pag_incorreto, cpfs_errados, compv_nao_env)     
    
    return modelos_enviados

  
