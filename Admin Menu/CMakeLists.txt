cmake_minimum_required(VERSION 3.10)
project(SolarOSD) # Переименовал проект, чтобы соответствовать сути

set(CMAKE_CXX_STANDARD 20)

# Конфигурация Kiero
add_compile_definitions(KIERO_INCLUDE_D3D11=1 KIERO_USE_MINHOOK=1)

# Настройка статической линковки (чтобы работало у всех без установки доп. софта)
if(MSVC)
    # Заменяем /MD на /MT во всех флагах компиляции
    foreach(flag_var
        CMAKE_CXX_FLAGS CMAKE_CXX_FLAGS_DEBUG CMAKE_CXX_FLAGS_RELEASE
        CMAKE_CXX_FLAGS_MINSIZEREL CMAKE_CXX_FLAGS_RELWITHDEBINFO
        CMAKE_C_FLAGS CMAKE_C_FLAGS_DEBUG CMAKE_C_FLAGS_RELEASE
        CMAKE_C_FLAGS_MINSIZEREL CMAKE_C_FLAGS_RELWITHDEBINFO)
        if(${flag_var} MATCHES "/MD")
            string(REGEX REPLACE "/MD" "/MT" ${flag_var} "${${flag_var}}")
        endif()
    endforeach()

    # Оптимизация размера и подавление варнингов
    add_compile_options(/wd4309 /wd4369 /wd4244 /wd4267 /wd4005 /O2 /GL)
    add_link_options(/LTCG /OPT:REF /OPT:ICF)
endif()

set(PROJECT_SOURCES
    "main.cpp"
    "osd.cpp"
    "osd.h"
    
    # SDK
    "../dump/CppSDK/SDK/Basic.cpp"
    "../dump/CppSDK/SDK/CoreUObject_functions.cpp"
    "../dump/CppSDK/SDK/Engine_functions.cpp"
    "../dump/CppSDK/SDK/FPVKamikazeDrone_functions.cpp"
    
    # Библиотеки
    "../libs/imgui/imgui.cpp"
    "../libs/imgui/imgui_draw.cpp"
    "../libs/imgui/imgui_widgets.cpp"
    "../libs/imgui/imgui_tables.cpp"
    "../libs/imgui/backends/imgui_impl_win32.cpp"
    "../libs/imgui/backends/imgui_impl_dx11.cpp"
    "../libs/kiero/kiero.cpp"
    "../libs/minhook/src/hook.c"
    "../libs/minhook/src/buffer.c"
    "../libs/minhook/src/trampoline.c"
    "../libs/minhook/src/hde/hde32.c"
    "../libs/minhook/src/hde/hde64.c"
)

add_library(SolarOSD SHARED ${PROJECT_SOURCES} )

target_include_directories(SolarOSD PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "../dump/CppSDK/SDK"
    "../dump/CppSDK"
    "../libs"
    "../libs/minhook/include"
    "../libs/imgui"
    "../libs/kiero"
)

target_link_libraries(SolarOSD PRIVATE kernel32 user32 d3d11 dxgi)