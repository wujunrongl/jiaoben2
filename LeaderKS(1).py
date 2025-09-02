#!/usr/bin/env python3
_L='version'
_K='message'
_J='success'
_I='base_name'
_H='Kuaishou'
_G='platform'
_F='architecture'
_E='python_version'
_D='utf-8'
_C=False
_B=True
_A=None
import platform,sys,os,subprocess,shutil,importlib.util,requests,hashlib,json,time,asyncio,logging,functools
from typing import Optional,Tuple,Dict,Any,Union,Callable
from urllib.parse import urljoin
from dataclasses import dataclass
from pathlib import Path
logging.basicConfig(level=logging.INFO,format='%(message)s',handlers=[logging.StreamHandler(),logging.FileHandler('leaderks.log',encoding=_D)])
logger=logging.getLogger(__name__)
def performance_monitor(func):
        '性能监控装饰器';A=func
        @functools.wraps(A)
        def B(*D,**E):
                C=time.time()
                try:F=A(*D,**E);B=time.time()-C;logger.debug(f"{A.__name__} 执行耗时: {B:.3f} 秒");return F
                except Exception as G:B=time.time()-C;logger.error(f"{A.__name__} 执行失败，耗时: {B:.3f} 秒，错误: {G}");raise
        return B
def retry_on_failure(max_retries=3,delay=1.):
        '重试装饰器';B=max_retries
        def A(func):
                A=func
                @functools.wraps(A)
                def C(*F,**G):
                        C=_A
                        for D in range(B):
                                try:return A(*F,**G)
                                except Exception as E:
                                        C=E
                                        if D<B-1:logger.warning(f"{A.__name__} 第 {D+1} 次尝试失败: {E}");time.sleep(delay)
                                        else:logger.error(f"{A.__name__} 所有尝试都失败了")
                        raise C
                return C
        return A
@dataclass
class ServerConfig:'服务器配置';base_url:str='http://154.12.60.33:2424';download_endpoint:str='/api/download_so.php';check_update_endpoint:str='/api/check_update.php';timeout:int=30;retry_times:int=3;chunk_size:int=8192;retry_delay:int=2
@dataclass
class UpdateConfig:'更新配置';auto_update:bool=_B;ask_confirmation:bool=_C;backup_old_files:bool=_B;delete_backup_after_success:bool=_B
@dataclass
class SystemInfo:'系统信息';architecture:str;python_version_tag:str;platform_info:str;python_version:str
class FileManager:
        '文件管理类'
        def __init__(A,base_dir=_A):B=base_dir;A.base_dir=Path(B)if B else Path(__file__).parent;A.version_file=A.base_dir/'version.json'
        def get_version_info_path(A):'获取版本信息文件路径';return A.version_file
        def save_version_info(A,version_info):
                '保存版本信息到本地文件'
                try:
                        with open(A.version_file,'w',encoding=_D)as B:json.dump(version_info,B,ensure_ascii=_C,indent=2)
                        return _B
                except Exception as C:return _C
        def load_version_info(A):
                '从本地文件加载版本信息'
                if A.version_file.exists():
                        try:
                                with open(A.version_file,'r',encoding=_D)as B:return json.load(B)
                        except Exception as C:logger.error(f"加载版本信息失败: {C}")
        def calculate_file_hash(E,file_path):
                '计算文件的MD5哈希值'
                try:
                        A=hashlib.md5()
                        with open(file_path,'rb')as B:
                                for C in iter(lambda:B.read(4096),b''):A.update(C)
                        return A.hexdigest()
                except Exception as D:logger.error(f"计算文件哈希失败: {D}");return
        def backup_file(D,file_path,suffix='.backup'):
                '备份文件';B=file_path
                try:
                        A=B.with_suffix(B.suffix+suffix)
                        if A.exists():A.unlink()
                        shutil.move(str(B),str(A));logger.info(f"已备份文件: {A}");return A
                except Exception as C:logger.error(f"备份文件失败: {C}");return
        def restore_file(C,backup_path,original_path):
                '恢复文件';A=original_path
                try:shutil.move(str(backup_path),str(A));logger.info(f"已恢复文件: {A}");return _B
                except Exception as B:logger.error(f"恢复文件失败: {B}");return _C
class NetworkManager:
        '网络管理类'
        def __init__(A,config):A.config=config;A.session=requests.Session();A.session.headers.update({'User-Agent':'LeaderKS/2.0'})
        @performance_monitor
        def check_server_update(self,base_name,py_ver_tag,arch,current_version=_A):
                '检查服务器是否有更新版本';A=self
                try:
                        E=urljoin(A.config.base_url,A.config.check_update_endpoint);F={_I:base_name,_E:py_ver_tag,_F:arch,'current_version':current_version,_G:platform.platform()};D=A.session.post(E,json=F,timeout=A.config.timeout);D.raise_for_status();B=D.json()
                        if B.get(_J):return B.get('data')
                        else:logger.error(f"服务器返回错误: {B.get(_K,'未知错误')}");return
                except requests.exceptions.RequestException as C:logger.error(f"网络请求失败: {C}");return
                except Exception as C:logger.error(f"检查更新时发生错误: {C}");return
        def request_so_download(A,base_name,py_ver_tag,arch):
                '向服务器请求SO文件下载链接'
                try:
                        G=urljoin(A.config.base_url,A.config.download_endpoint);H={_I:base_name,_E:py_ver_tag,_F:arch,_G:platform.platform(),'client_info':{_E:sys.version,_G:platform.platform(),_F:arch}};D=A.session.post(G,json=H,timeout=A.config.timeout);D.raise_for_status();B=D.json()
                        if B.get(_J):
                                E=B.get('data',{});F=E.get('download_url');I=E.get('version_info',{})
                                if F:return F,I
                                else:logger.error('服务器未提供下载链接');return _A,_A
                        else:logger.error(f"服务器返回错误: {B.get(_K,'未知错误')}");return _A,_A
                except requests.exceptions.RequestException as C:logger.error(f"网络请求失败: {C}");return _A,_A
                except Exception as C:logger.error(f"请求下载时发生错误: {C}");return _A,_A
        @performance_monitor
        def download_so_file(self,base_name,py_ver_tag,arch,download_url):
                '从服务器下载SO文件';P='所有重试都失败了';O='content-md5';N='http://154.12.60.33/';B=download_url;A=self;logger.info('开始下载SO文件')
                if B.startswith(N)and':2424'not in B:B=B.replace(N,'http://154.12.60.33:2424/');logger.info(f"修正后的下载地址: {B}")
                F=f"{base_name}.cpython-{py_ver_tag}-{arch}-linux-gnu.so";C=f"{F}.tmp"
                for D in range(A.config.retry_times):
                        try:
                                logger.info(f"下载尝试 {D+1}/{A.config.retry_times}");E=A.session.get(B,stream=_B,timeout=A.config.timeout);E.raise_for_status();K=int(E.headers.get('content-length',0));G=0
                                with open(C,'wb')as H:
                                        for I in E.iter_content(chunk_size=A.config.chunk_size):
                                                if I:
                                                        H.write(I);G+=len(I)
                                                        if K>0:Q=G/K*100;print(f"\r下载进度: {Q:.1f}%",end='',flush=_B)
                                        H.flush();os.fsync(H.fileno())
                                print(f"\n下载完成: {G} 字节")
                                if O in E.headers:
                                        L=E.headers[O];M=A._calculate_temp_file_hash(C)
                                        if L!=M:
                                                logger.error(f"文件校验失败: 期望 {L}, 实际 {M}")
                                                if D<A.config.retry_times-1:logger.info('重试下载...');continue
                                                else:os.remove(C);return
                                os.rename(C,F);return os.path.abspath(F)
                        except requests.exceptions.RequestException as J:
                                logger.error(f"下载失败 (尝试 {D+1}): {J}");A._cleanup_temp_file(C)
                                if D<A.config.retry_times-1:logger.info(f"等待 {A.config.retry_delay} 秒后重试...");time.sleep(A.config.retry_delay)
                                else:logger.error(P);return
                        except Exception as J:
                                logger.error(f"下载时发生错误 (尝试 {D+1}): {J}");A._cleanup_temp_file(C)
                                if D<A.config.retry_times-1:logger.info(f"等待 {A.config.retry_delay} 秒后重试...");time.sleep(A.config.retry_delay)
                                else:logger.error(P);return
        def _calculate_temp_file_hash(E,temp_filename):
                '计算临时文件的哈希值'
                try:
                        A=hashlib.md5()
                        with open(temp_filename,'rb')as B:
                                for C in iter(lambda:B.read(4096),b''):A.update(C)
                        return A.hexdigest()
                except Exception as D:logger.error(f"计算临时文件哈希失败: {D}");return
        def _cleanup_temp_file(C,temp_filename):
                '清理临时文件';A=temp_filename
                if os.path.exists(A):
                        try:os.remove(A)
                        except Exception as B:logger.warning(f"清理临时文件失败: {B}")
class SystemInfoManager:
        '系统信息管理类'
        @staticmethod
        def get_system_architecture():'获取当前系统的架构';B='aarch64';A='x86_64';C=platform.machine().lower();D={A:A,'amd64':A,B:B,'arm64':B};return D.get(C,C) 
        @staticmethod
        def get_python_version_tag():'获取与 .so 文件名兼容的 Python 版本标签';A,B=sys.version_info.major,sys.version_info.minor;return f"{A}{B}"
        @staticmethod
        def get_system_info():'获取完整的系统信息';return SystemInfo(architecture=SystemInfoManager.get_system_architecture(),python_version_tag=SystemInfoManager.get_python_version_tag(),platform_info=platform.platform(),python_version=sys.version)
class SOModuleLoader:
        'SO模块加载器'
        def __init__(A,file_manager):A.file_manager=file_manager
        def find_so_file(B,base_name,py_ver_tag,arch,auto_download=_B,network_manager=_A):
                '查找SO文件，如果不存在则尝试下载';G=auto_download;E=arch;D=py_ver_tag;C=base_name;A=network_manager;H=f"{C}.cpython-{D}-{E}-linux-gnu.so";F=Path(H).resolve()
                if F.is_file():
                        if G and A:return B._handle_update_check(C,D,E,F,A)
                        return str(F)
                else:
                        logger.warning(f"未找到预期的 SO 文件: {H}")
                        if G and A:return B._handle_download(C,D,E,A)
                        B._list_so_files();return
        def _handle_update_check(B,base_name,py_ver_tag,arch,full_path,network_manager):
                '处理更新检查';F=network_manager;E=full_path;D=py_ver_tag;C=base_name;logger.info('检查是否需要更新...');G=B.file_manager.load_version_info();H=G.get(_L)if G else _A;A=F.check_server_update(C,D,arch,H)
                if A and A.get('has_update'):logger.info(f"发现新版本: {A.get('latest_version')}");logger.info(f"更新说明: {A.get('update_description','无')}");return B._perform_update(C,D,arch,E,F)
                return str(E)
        def _handle_download(F,base_name,py_ver_tag,arch,network_manager):
                '处理下载';D=network_manager;C=arch;B=py_ver_tag;A=base_name;logger.info('尝试从服务器下载SO文件...');G=F.file_manager.load_version_info();J=G.get(_L)if G else _A;K=D.check_server_update(A,B,C,J);H,I=D.request_so_download(A,B,C)
                if H:
                        E=D.download_so_file(A,B,C,H)
                        if E and Path(E).is_file():
                                if I:F.file_manager.save_version_info(I)
                                return E
                        else:logger.error('下载失败')
                else:logger.error('无法获取下载链接')
        def _perform_update(A,base_name,py_ver_tag,arch,full_path,network_manager):
                '执行更新';J='update_config';G=network_manager;F=py_ver_tag;E=base_name;C=full_path;logger.info('开始下载更新...');H,I=G.request_so_download(E,F,arch)
                if H:
                        B=_A
                        if hasattr(A,J)and A.update_config.backup_old_files:B=A.file_manager.backup_file(C)
                        D=G.download_so_file(E,F,arch,H)
                        if D and Path(D).is_file():
                                logger.info(f"成功更新SO文件: {D}")
                                if I:A.file_manager.save_version_info(I)
                                if B and hasattr(A,J)and A.update_config.delete_backup_after_success:
                                        if B.exists():B.unlink();logger.info('已删除备份文件')
                                return D
                        else:
                                logger.error('更新失败，恢复旧文件')
                                if B:A.file_manager.restore_file(B,C)
                                return str(C)
                else:logger.error('无法获取更新下载链接');return str(C)
        def _list_so_files(C):
                '列出当前目录下的SO文件';logger.info('当前目录下的 .so 文件:')
                try:
                        for A in Path('.').glob('*.so'):logger.info(f"  - {A}")
                except Exception as B:logger.error(f"无法列出 .so 文件: {B}")
        def load_module(E,so_path,module_name):
                '加载SO模块';D=module_name
                try:
                        A=importlib.util.spec_from_file_location(D,so_path)
                        if A is _A:logger.error('无法创建模块规范');return
                        B=importlib.util.module_from_spec(A);sys.modules[D]=B;A.loader.exec_module(B);return B
                except ImportError as C:logger.error(f"ImportError: {C}");return
                except Exception as C:logger.error(f"加载时发生错误: {C}");return
        def call_function(I,module,function_name='main',args_list=_A):
                '调用模块中的函数';E=args_list;D=function_name;C=module
                try:
                        if hasattr(C,D):
                                A=getattr(C,D)
                                if E is _A:
                                        if asyncio.iscoroutinefunction(A):B=asyncio.run(A())
                                        else:B=A()
                                elif asyncio.iscoroutinefunction(A):B=asyncio.run(A(*E))
                                else:B=A(*E)
                                return B
                        else:
                                logger.error(f"未找到函数 '{D}'");F=[A for A in dir(C)if not A.startswith('_')]
                                for G in sorted(F):logger.info(f"  - {G}")
                                return
                except Exception as H:logger.error(f"调用函数时发生错误: {H}");return
class LeaderKS:
        '主控制器类'
        def __init__(A,config,update_config):C=update_config;B=config;A.config=B;A.update_config=C;A.file_manager=FileManager();A.network_manager=NetworkManager(B);A.system_info=SystemInfoManager.get_system_info();A.so_loader=SOModuleLoader(A.file_manager);A.so_loader.update_config=C;A._validate_config()
        def _validate_config(A):
                '验证配置的有效性'
                try:
                        if not A.config.base_url.startswith(('http://','https://')):logger.warning('服务器地址格式可能不正确')
                        if A.config.timeout<=0:logger.warning('超时时间应该大于0');A.config.timeout=30
                        if A.config.retry_times<=0:logger.warning('重试次数应该大于0');A.config.retry_times=3
                        if A.update_config.auto_update and not A.update_config.backup_old_files:logger.warning('自动更新时建议启用文件备份')
                except Exception as B:logger.error(f"配置验证失败: {B}")
        def diagnose_environment(A):'诊断运行环境';logger.info('--- 环境诊断 ---');logger.info(f"Python 版本: {sys.version}");logger.info(f"平台详细信息: {A.system_info.platform_info}");logger.info(f"系统架构: {A.system_info.architecture}");logger.info(f"Python 版本标签: {A.system_info.python_version_tag}");A._check_dependencies()
        def _check_dependencies(B):
                '检查关键依赖'
                try:import requests as A;logger.info(f"✓ requests 版本: {A.__version__}")
                except ImportError:logger.error('✗ requests 依赖未安装')
                try:import asyncio;logger.info('✓ asyncio 可用')
                except ImportError:logger.error('✗ asyncio 依赖不可用')
        def run(A,so_base_name=_H,custom_args=_A):
                '运行主程序';C=so_base_name;F=time.time()
                try:
                        logger.info(f"开始运行 LeaderKS");A.diagnose_environment();D=A.so_loader.find_so_file(C,A.system_info.python_version_tag,A.system_info.architecture,auto_download=A.update_config.auto_update,network_manager=A.network_manager)
                        if not D:logger.error('致命错误: 找不到 .so 文件');return 1
                        logger.info('开始加载SO模块...');E=A._load_module_with_fallback(D,C)
                        if E is _A:logger.error('所有加载方法都失败了');return 2
                        B=A.so_loader.call_function(E,'main',custom_args);G=time.time()-F;logger.info(f"程序执行完成，耗时: {G:.2f} 秒")
                        if B is not _A:logger.info(f"脚本退出码: {B}");return B
                        else:logger.info('脚本退出码: 2');return 2
                except KeyboardInterrupt:logger.info('程序被用户中断');return 130
                except Exception as H:logger.error(f"程序运行出错: {H}");import traceback as I;logger.error(f"详细错误信息: {I.format_exc()}");return 1
        def _load_module_with_fallback(D,so_file_path,so_base_name):
                '使用多种方法尝试加载模块';E=so_file_path;C=so_base_name;A=D.so_loader.load_module(E,C)
                if A is _A:
                        F=[_H,'kuaishou',C.lower()]
                        for B in F:
                                if A is _A and B!=C:
                                        logger.info(f"尝试使用模块名: {B}");A=D.so_loader.load_module(E,B)
                                        if A:logger.info(f"成功使用模块名 '{B}' 加载模块");break
                return A
def create_default_config():
        '创建默认配置';D='LEADERKS_AUTO_UPDATE';C='LEADERKS_SERVER_URL';A=ServerConfig();B=UpdateConfig()
        if os.getenv(C):A.base_url=os.getenv(C)
        if os.getenv(D):B.auto_update=os.getenv(D).lower()=='true'
        return A,B
def main():
        '主函数'
        try:A,B=create_default_config();C=LeaderKS(A,B);D=C.run(_H);sys.exit(D)
        except Exception as E:logger.error(f"程序启动失败: {E}");sys.exit(1)
if __name__=='__main__':main()