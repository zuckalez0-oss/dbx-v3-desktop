# PROD Release Checklist

## 1. Supabase PROD

- criar ou revisar o projeto Supabase de produção
- confirmar `Project URL`
- confirmar `anon public key`
- confirmar `Email provider` habilitado
- confirmar cadastro público desabilitado
- confirmar templates de email revisados
- confirmar SMTP de produção
- confirmar tabela `public.profiles` '
- confirmar trigger de criação de perfil
- confirmar `RLS` habilitado
- confirmar policies aplicadas

## 2. Onboarding de usuários

- definir processo interno de criação de usuário
- definir padrão de `username`/nick
- definir quem pode liberar `dbx_access`
- definir quem pode marcar `desktop_access = true`
- definir política de status (`active`, `trial`, `blocked`)

## 3. Configuração do EXE

- gerar config real de produção
- validar `SUPABASE_URL`
- validar `SUPABASE_ANON_KEY`
- validar `profiles_table`
- validar `profile_lookup_column`
- validar status permitidos

## 4. Validação funcional antes do push

- login com usuário ativo
- restauração de sessão ao reabrir o EXE
- logout e retorno à tela de login
- usuário sem `dbx_access` bloqueado
- usuário com `desktop_access = false` bloqueado
- usuário com `status = blocked` bloqueado
- saudação `Olá, <nick>`
- recuperação de senha

## 5. UX final

- tela de login sem termos técnicos de infraestrutura
- botão `Encerrar Sessão` destacado em vermelho
- nome amigável do usuário exibido corretamente
- mensagens de erro claras para operação

## 6. Push / GitHub

- revisar `git status`
- revisar diff final
- validar branch de homologação
- fazer commit com mensagem clara
- push da branch
- abrir PR para revisão

## 7. Build de produção

- atualizar dependências locais
- rodar `build_desktop.ps1`
- validar saída em `dist`
- testar o EXE buildado em ambiente limpo
- validar login real no binário final
- validar exportações já existentes

## 8. Go-live

- congelar config final do Supabase PROD
- criar primeiros usuários
- validar primeiro login em produção
- validar sessão persistida
- registrar procedimento de suporte
