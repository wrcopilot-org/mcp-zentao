
@echo off

set SVN_TB=2544
set pjdir=E:\checkcode\epm\main
set dir1=%pjdir%\log\cur
set dir2=%pjdir%\log\builded
set dir3=%pjdir%\log\temp

md %pjdir%\log
md %dir1%
md %dir2%
md %dir3%


set BROOT=%pjdir%
set TBNET=_EPM_main

cd /d %BROOT%\%TBNET%
call svn log -r head:r%SVN_TB% >%dir1%\dc_commit.log

for %%f in (%dir1%\*.*) do (
    if exist "%dir2%\%%~nxf" (
        fc /b "%dir1%\%%~nxf" "%dir2%\%%~nxf" > nul
        if errorlevel 1 (
             echo The file %%~nxf is different.
			goto :codechg
        ) else (
             echo The file %%~nxf is identical.
        )
    ) else (
		echo "no file " %%~nxf
		goto :codechg
	)
)

goto :nobuild

set DELAY_TIME=5  :: 延时等待秒数

:wait_code_commit_finish
:codechg
timeout /t %DELAY_TIME% /nobreak > nul


call svn log -r head:r%SVN_TB% >%dir3%\dc_commit.log

for %%f in (%dir1%\*.*) do (
    if exist "%dir3%\%%~nxf" (
        fc /b "%dir1%\%%~nxf" "%dir3%\%%~nxf" > nul
        if errorlevel 1 (
             echo The file %%~nxf is different.
			goto :wait_code_commit_finish
        ) else (
             echo The file %%~nxf is identical.
        )
    ) else (
		echo "no file " %%~nxf

	)
)

copy /Y %dir3% %dir1%

echo "code chg"

"C:\Program Files (x86)\VisBuildPro8\VisBuildCmd.exe" /b  "%pjdir%\Builder.bld"
if errorlevel == 0 (
	copy /Y %dir1% %dir2%
)

goto :buildend


:nobuild
chcp 65001

echo "nobuild"
echo "代码编译：DC 代码没有改变 "

rem call D:\tools\rd-dingding\SendPost.exe -s "sss" -d "代码编译：DC 代码没有改变 "
goto :buildend



:buildend

cd E:\code\epm\checkcode
